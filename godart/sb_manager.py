# godart/sb_manager.py
from supabase import create_client, Client

from .config import Config





class SupabaseManager:
    def __init__(self):
        Config.validate()
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        self._model_cache = {}
        self._context_cache = {}
    
    def get_model_config(self, model_alias):
        if model_alias in self._model_cache:
            return self._model_cache[model_alias]
        
        try:
            response = self.client.rpc('get_godart_model_config', {
                'p_model_alias': model_alias
            }).execute()
            
            if response.data and len(response.data) > 0:
                config = response.data[0]
                self._model_cache[model_alias] = config
                return config
            return None
        except Exception as e:
            print(f"[!!] Error al obtener configuración del modelo: {e}")
            return None
    
    def get_context(self, context_key):
        if context_key in self._context_cache:
            return self._context_cache[context_key]
        
        try:
            response = self.client.rpc('get_godart_context', {
                'p_context_key': context_key
            }).execute()
            
            if response.data and len(response.data) > 0:
                context = response.data[0]['context_content']
                self._context_cache[context_key] = context
                return context
            return None
        except Exception as e:
            print(f"[!!] Error al obtener contexto: {e}")
            return None
    
    def get_identity(self):
        return self.get_context('identity_default')
    
    def get_tone(self, tone_key):
        if not tone_key or tone_key == 'default':
            return None
        return self.get_context(tone_key)
    
    def get_all_tones(self):
        try:
            response = self.client.rpc('get_all_godart_tones').execute()
            if response.data:
                return {item['context_key']: item['context_content'] for item in response.data}
            return {}
        except Exception as e:
            print(f"[!!] Error al obtener tonos: {e}")
            return {}
    
    def get_next_available_key(self):
        try:
            response = self.client.rpc('get_next_available_godart_key').execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[!!] Error al obtener API key: {e}")
            return None
    
    def get_all_available_keys(self):
        try:
            response = self.client.rpc('get_all_available_godart_keys').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"[!!] Error al obtener API keys: {e}")
            return []
    
    def log_request(self, key_id, success, error_message=None, model=None):
        try:
            self.client.rpc('log_godart_request', {
                'p_key_id': str(key_id),
                'p_success': success,
                'p_error_message': error_message,
                'p_model': model or Config.DEFAULT_MODEL
            }).execute()
        except Exception as e:
            print(f"[!!] Error al registrar log: {e}")
    
    def get_statistics(self):
        try:
            response = self.client.rpc('get_godart_keys_stats').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"[!!] Error: {e}")
            return []