# Godart AI (Privado... por ahora)
Sistema de IA desarrollado por Rodolfo Casan con manejo inteligente y múltiples tonos de personalidad.





## Instalación
### Desde GitHub
```bash
pip3 install --upgrade git+https://github.com/rodolfocasan/godart.git
```

### Desde carpeta local
Si ya tienes el repositorio clonado:
```bash
cd godart
pip3 install -e .
```





## Requisitos
- Python 3.10 o superior
- Cuenta de Supabase configurada con las funciones RPC necesarias





## Uso Básico
### Configuración inicial
```python
import godart
from godart import Config, SupabaseManager, GodartManager

# Configurar credenciales de Supabase
Config.configure(
    supabase_url = "tu_supabase_url",
    supabase_service_key = "tu_supabase_service_key"
)

# O de forma individual
Config.set_supabase_url("tu_supabase_url")
Config.set_supabase_service_key("tu_supabase_service_key")

# Inicializar managers
supabase = SupabaseManager()
godart = GodartManager(supabase)
```

### Request simple
```python
# Sin tono específico
respuesta = godart.make_request("¿Cuál es la capital de Francia?")
print(respuesta)

# Con tono formal
respuesta = godart.make_request(
    "Explícame la fotosíntesis",
    tono = 'formal'
)
print(respuesta)

# Con tono sin censura
respuesta = godart.make_request(
    "Dame tu opinión honesta sobre esto",
    tono = 'sin_censura'
)
print(respuesta)
```

### Chat con historial
```python
# Crear una sesión de chat
session_id = "mi_conversacion"

# Primera interacción
respuesta1 = godart.make_request_chat(
    "Hola, soy desarrollador Python",
    session_id = session_id,
    tono = 'tecnico'
)
print(respuesta1)

# Segunda interacción (con contexto)
respuesta2 = godart.make_request_chat(
    "¿Qué patrones de diseño me recomiendas?",
    session_id = session_id,
    tono = 'tecnico'
)
print(respuesta2)

# Ver historial
historial = godart.get_chat_history(session_id)

# Limpiar sesión
godart.clear_chat_session(session_id)
```





## Tonos disponibles
- `None` o `'default'`: Sin tono específico
- `'formal'`: Profesional, ejecutivo, preciso
- `'sin_censura'`: Libertad total, honesto sin filtros
- `'casual'`: Conversacional y relajado
- `'tecnico'`: Enfoque técnico detallado (ideal para desarrolladores o ingenieros)
- `'empatico'`: Comprensivo y empático





## Modelos disponibles
- `mini` (por defecto): Modelo rápido y eficiente
- `base`: Modelo balanceado
- `max`: Modelo más potente
```python
respuesta = godart.make_request(
    "Tu pregunta aquí",
    model = 'max',
    tono = 'tecnico'
)
```





## Características
### Estadísticas
```python
# Ver estadísticas de uso de API keys
stats = supabase.get_statistics()
for stat in stats:
    print(f"Cuenta: {stat['account_name']}")
    print(f"Requests hoy: {stat['requests_today']}/{stat['daily_limit']}")
    print(f"Tasa de éxito: {stat['success_rate']}%")
```





### Configuración personalizada
```python
custom_config = {
    'temperature': 0.9,
    'max_output_tokens': 3000,
    'top_p': 0.95
}

respuesta = godart.make_request(
    "Tu pregunta",
    custom_config = custom_config
)
```





## Autor
Rodolfo Casan