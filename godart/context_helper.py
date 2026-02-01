# godart/context_helper.py
from datetime import datetime





def obtener_hora_actual():
    return datetime.now().strftime("%H:%M:%S")

def obtener_fecha_actual():
    return datetime.now().strftime("%Y-%m-%d")