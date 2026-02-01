# godart/godart_manager.py
import time
from google import genai
from collections import deque
from google.genai import types

from .config import Config
from .sb_manager import SupabaseManager





class RateLimitTracker:
    def __init__(self, rpm_limit, tpm_limit):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        
        self.request_times = deque()
        self.token_usage = deque()
    
    def _clean_old_entries(self):
        current_time = time.time()
        cutoff_time = current_time - 60
        
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()
        
        while self.token_usage and self.token_usage[0]['timestamp'] < cutoff_time:
            self.token_usage.popleft()
    
    def can_make_request(self, estimated_tokens=0):
        self._clean_old_entries()
        
        if len(self.request_times) >= self.rpm_limit:
            return False, "RPM"
        
        current_tokens = sum(entry['tokens'] for entry in self.token_usage)
        if current_tokens + estimated_tokens > self.tpm_limit:
            return False, "TPM"
        return True, None
    
    def record_request(self, tokens_used):
        current_time = time.time()
        
        self.request_times.append(current_time)
        self.token_usage.append({
            'timestamp': current_time,
            'tokens': tokens_used
        })
        self._clean_old_entries()
    
    def get_wait_time(self, limit_type):
        if limit_type == "RPM":
            if self.request_times:
                oldest_request = self.request_times[0]
                wait_time = 60 - (time.time() - oldest_request)
                return max(0, wait_time)
        elif limit_type == "TPM":
            if self.token_usage:
                oldest_token = self.token_usage[0]['timestamp']
                wait_time = 60 - (time.time() - oldest_token)
                return max(0, wait_time)
        return 0
    
    def get_current_usage(self):
        self._clean_old_entries()
        current_tokens = sum(entry['tokens'] for entry in self.token_usage)
        return {
            'requests': len(self.request_times),
            'tokens': current_tokens,
            'rpm_limit': self.rpm_limit,
            'tpm_limit': self.tpm_limit
        }





class GodartManager:
    def __init__(self, supabase_manager: SupabaseManager):
        self.supabase = supabase_manager
        self.current_key = None
        self.current_key_id = None
        self.current_account = None
        self.client = None
        self.chat_sessions = {}
        
        self.rate_trackers = {}
        self.attempted_keys = set()
    
    def _get_model_real_name(self, model_alias):
        model_config = self.supabase.get_model_config(model_alias)
        if model_config:
            return model_config['model_real_name']
        return None
    
    def _get_rate_limits(self, model_alias):
        model_config = self.supabase.get_model_config(model_alias)
        if model_config:
            return {
                'rpm': model_config['rpm_limit'],
                'tpm': model_config['tpm_limit'],
                'rpd': model_config['rpd_limit']
            }
        return {'rpm': 10, 'tpm': 100000, 'rpd': 500}
    
    def _get_or_create_tracker(self, key_id, model_alias):
        if key_id not in self.rate_trackers:
            limits = self._get_rate_limits(model_alias)
            self.rate_trackers[key_id] = RateLimitTracker(
                rpm_limit = limits['rpm'],
                tpm_limit = limits['tpm']
            )
        return self.rate_trackers[key_id]
    
    def _estimate_tokens(self, prompt):
        if isinstance(prompt, str):
            return len(prompt) // 4
        return 500
    
    def _build_system_instruction(self, identidad=None, tono=None):
        identity = identidad if identidad else self.supabase.get_identity()
        
        if not identity:
            raise Exception("[!!] No se pudo obtener la identidad desde Supabase")
        
        if tono:
            tone_content = self.supabase.get_tone(tono)
            if tone_content:
                return f"{identity}\n\n{tone_content}"
        
        return identity
    
    def get_available_key(self, model=None, estimated_tokens=0):
        model = model or Config.DEFAULT_MODEL
        
        all_keys = self.supabase.get_all_available_keys()
        
        if not all_keys:
            print("[!!] No hay API keys disponibles en el pool")
            return False
        
        available_keys = [k for k in all_keys if k['key_id'] not in self.attempted_keys]
        
        if not available_keys:
            print("[!!] Se agotaron todas las API keys disponibles")
            return False
        
        for key_data in available_keys:
            key_id = key_data['key_id']
            tracker = self._get_or_create_tracker(key_id, model)
            
            can_request, limit_type = tracker.can_make_request(estimated_tokens)
            
            if can_request:
                self.current_key = key_data['api_key']
                self.current_key_id = key_id
                self.current_account = key_data['account_name']
                self.client = genai.Client(api_key=self.current_key)
                
                self.attempted_keys.add(key_id)
                
                usage = tracker.get_current_usage()
                print(f" - Usando: {self.current_account} | RPM: {usage['requests']}/{usage['rpm_limit']} | TPM: {usage['tokens']}/{usage['tpm_limit']}")
                return True
            else:
                wait_time = tracker.get_wait_time(limit_type)
                print(f" - {key_data['account_name']}: Límite {limit_type} alcanzado. Espera: {wait_time:.1f}s")
        
        min_wait = float('inf')
        for key_data in available_keys:
            key_id = key_data['key_id']
            tracker = self._get_or_create_tracker(key_id, model)
            _, limit_type = tracker.can_make_request(estimated_tokens)
            if limit_type:
                wait = tracker.get_wait_time(limit_type)
                min_wait = min(min_wait, wait)
        
        if min_wait < float('inf') and min_wait > 0:
            print(f" - Todas las keys en límite. Menor espera: {min_wait:.1f}s")
        return False
    
    def _get_generation_config(self, tono=None, custom_config=None):
        tone_key = tono if tono else 'default'
        config_params = Config.TONE_CONFIGS.get(tone_key, Config.TONE_CONFIGS['default'])
        
        if custom_config:
            config_params = {**config_params, **custom_config}
        
        return types.GenerateContentConfig(
            temperature = config_params.get('temperature', Config.DEFAULT_TEMPERATURE),
            top_p = config_params.get('top_p', Config.DEFAULT_TOP_P),
            top_k = config_params.get('top_k', Config.DEFAULT_TOP_K),
            max_output_tokens = config_params.get('max_output_tokens', Config.DEFAULT_MAX_OUTPUT_TOKENS),
            stop_sequences = custom_config.get('stop_sequences') if custom_config else None
        )
    
    def make_request(self, prompt, model=None, identidad=None, tono=None, custom_config=None):
        model_alias = model or Config.DEFAULT_MODEL
        model_real = self._get_model_real_name(model_alias)
        
        if not model_real:
            raise Exception(f"[!!] Modelo '{model_alias}' no configurado en Supabase")
        
        system_instruction = self._build_system_instruction(identidad, tono)
        
        self.attempted_keys.clear()
        
        estimated_tokens = self._estimate_tokens(prompt)
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                if not self.client and not self.get_available_key(model_alias, estimated_tokens):
                    if not self.get_available_key(model_alias, estimated_tokens):
                        raise Exception("[!!] No hay API keys disponibles que puedan procesar este request")
                
                config = self._get_generation_config(tono, custom_config)
                config.system_instruction = system_instruction
                
                response = self.client.models.generate_content(
                    model = model_real,
                    contents = prompt,
                    config = config
                )
                
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    total_tokens = usage.total_token_count
                    
                    tracker = self._get_or_create_tracker(self.current_key_id, model_alias)
                    tracker.record_request(total_tokens)
                    
                    print(f" - Tokens: in={usage.prompt_token_count} out={usage.candidates_token_count} total={total_tokens}")
                else:
                    tracker = self._get_or_create_tracker(self.current_key_id, model_alias)
                    tracker.record_request(estimated_tokens)
                
                self.supabase.log_request(self.current_key_id, True, model=model_alias)
                return response.text
            except Exception as e:
                error_msg = str(e)
                self.supabase.log_request(self.current_key_id, False, error_msg, model_alias)
                
                if any(x in error_msg.lower() for x in ['429', 'quota', 'resource_exhausted']):
                    print(f"[!!] Key agotada: {self.current_account}")
                    
                    self.client = None
                    
                    if attempt < Config.MAX_RETRIES - 1:
                        print(" - Rotando a siguiente key del pool...")
                        time.sleep(1)
                        continue
                raise e
        raise Exception("[!!] Todas las API keys del pool están agotadas")
    
    def make_request_chat(self, message, session_id="default", model=None, identidad=None, tono=None, history=None, custom_config=None):
        model_alias = model or Config.DEFAULT_MODEL
        model_real = self._get_model_real_name(model_alias)
        
        if not model_real:
            raise Exception(f"[!!] Modelo '{model_alias}' no configurado en Supabase")
        
        system_instruction = self._build_system_instruction(identidad, tono)
        
        self.attempted_keys.clear()
        
        estimated_tokens = self._estimate_tokens(message)
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                if not self.client and not self.get_available_key(model_alias, estimated_tokens):
                    if not self.get_available_key(model_alias, estimated_tokens):
                        raise Exception("[!!] No hay API keys disponibles que puedan procesar este request")
                
                if session_id not in self.chat_sessions:
                    config = self._get_generation_config(tono, custom_config)
                    config.system_instruction = system_instruction
                    
                    self.chat_sessions[session_id] = self.client.chats.create(
                        model = model_real,
                        config = config,
                        history = history or []
                    )
                
                chat = self.chat_sessions[session_id]
                response = chat.send_message(message)
                
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    total_tokens = usage.total_token_count
                    
                    tracker = self._get_or_create_tracker(self.current_key_id, model_alias)
                    tracker.record_request(total_tokens)
                    
                    print(f" - Tokens: in={usage.prompt_token_count} out={usage.candidates_token_count} total={total_tokens}")
                else:
                    tracker = self._get_or_create_tracker(self.current_key_id, model_alias)
                    tracker.record_request(estimated_tokens)
                
                self.supabase.log_request(self.current_key_id, True, model=model_alias)
                return response.text
            except Exception as e:
                error_msg = str(e)
                self.supabase.log_request(self.current_key_id, False, error_msg, model_alias)
                
                if any(x in error_msg.lower() for x in ['429', 'quota', 'resource_exhausted']):
                    print(f"[!!] Key agotada: {self.current_account}")
                    
                    if session_id in self.chat_sessions:
                        saved_history = self.chat_sessions[session_id].get_history()
                        del self.chat_sessions[session_id]
                    else:
                        saved_history = None
                    
                    self.client = None
                    
                    if attempt < Config.MAX_RETRIES - 1:
                        if saved_history:
                            history = saved_history
                        print(" - Rotando a siguiente key del pool...")
                        time.sleep(1)
                        continue
                raise e
        raise Exception("[!!] Todas las API keys del pool están agotadas")
    
    def get_chat_history(self, session_id="default"):
        if session_id in self.chat_sessions:
            return self.chat_sessions[session_id].get_history()
        return []
    
    def clear_chat_session(self, session_id="default"):
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            return True
        return False
    
    def clear_all_sessions(self):
        self.chat_sessions.clear()