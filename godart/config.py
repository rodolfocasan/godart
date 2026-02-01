# godart/config.py





class Config:
    # Variables configurables
    SUPABASE_URL = None
    SUPABASE_SERVICE_KEY = None
    
    # Configuraciones por defecto
    DEFAULT_MODEL = "mini"
    MAX_RETRIES = 3
    
    # Configuraciones de generación optimizadas
    DEFAULT_TEMPERATURE = 0.85
    DEFAULT_TOP_P = 0.95
    DEFAULT_TOP_K = 40
    DEFAULT_MAX_OUTPUT_TOKENS = 2048
    
    # Configuraciones por tono
    TONE_CONFIGS = {
        'formal': {
            'temperature': 0.7,
            'top_p': 0.90,
            'max_output_tokens': 1536
        },
        'sin_censura': {
            'temperature': 0.95,
            'top_p': 0.95,
            'max_output_tokens': 2048
        },
        'casual': {
            'temperature': 0.9,
            'top_p': 0.95,
            'max_output_tokens': 1792
        },
        'tecnico': {
            'temperature': 0.75,
            'top_p': 0.92,
            'max_output_tokens': 2560
        },
        'empatico': {
            'temperature': 0.85,
            'top_p': 0.93,
            'max_output_tokens': 1792
        },
        'default': {
            'temperature': 0.85,
            'top_p': 0.95,
            'max_output_tokens': 2048
        }
    }
    
    @classmethod
    def set_supabase_url(cls, url):
        cls.SUPABASE_URL = url
    
    @classmethod
    def set_supabase_service_key(cls, key):
        cls.SUPABASE_SERVICE_KEY = key
    
    @classmethod
    def configure(cls, supabase_url, supabase_service_key):
        cls.SUPABASE_URL = supabase_url
        cls.SUPABASE_SERVICE_KEY = supabase_service_key
    
    @classmethod
    def validate(cls):
        if not cls.SUPABASE_URL or not cls.SUPABASE_SERVICE_KEY:
            raise ValueError("[!!] Faltan credenciales de Supabase. Usa Config.configure() o Config.set_supabase_url() y Config.set_supabase_service_key()")
        return True