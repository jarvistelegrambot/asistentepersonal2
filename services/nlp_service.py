import json
from groq import Groq
import config
import datetime

def get_client():
    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "tu_api_key_de_groq":
        return None
    return Groq(api_key=config.GROQ_API_KEY)

def transcribe_audio(file_path):
    """Transcribe un archivo de audio a texto usando Whisper-large-v3 en Groq."""
    client = get_client()
    if not client:
        return "Error: GROQ_API_KEY no configurada."
        
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3", 
                file=audio_file,
                response_format="json"
            )
        return transcript.text
    except Exception as e:
        print(f"Error transcribiendo audio: {e}")
        return f"Error transcribiendo el audio: {e}"

def extract_event_intent(text):
    """
    Usa Llama 3 (Groq) para extraer detalles de un evento.
    """
    client = get_client()
    if not client:
        return None
        
    now = datetime.datetime.now()
    system_prompt = (
        f"Eres un experto extrayendo intenciones de un asistente personal. "
        f"La fecha y hora actual es: {now.strftime('%Y-%m-%d %H:%M:%S')}. "
        f"Tu ÚNICA salida debe ser un objeto JSON válido. No incluyas texto fuera del JSON.\n"
        f"REGLAS DE INTENCIÓN:\n"
        f"1. Si el usuario quiere crear una cita o evento: Devuelve JSON con 'intent': 'create_event', 'summary' (título), 'start_time_iso' y 'end_time_iso'. Asume 1 hora de duración si no especifica fin.\n"
        f"2. Si el usuario quiere añadir algo a una lista de tareas o recordar algo sin fecha: Devuelve JSON con 'intent': 'add_todo', 'task' (descripción).\n"
        f"3. Si el usuario quiere añadir una suscripción o pago recurrente: Devuelve JSON con 'intent': 'add_subscription', 'sub_name' (nombre del servicio), 'sub_cost' (número float, usa null si no lo dice), y 'sub_day' (número entero del día de cobro, usa null si no lo dice).\n"
        f"4. Si el usuario dice que ha pasado la ITV, hecho la revisión del coche, o pagado el impuesto de circulación: Devuelve JSON con 'intent': 'update_vehicle', 'vehicle_event' (estrictamente 'itv', 'maintenance' o 'tax').\n"
        f"5. Si es imposible deducir la intención, devuelve {{}}."
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error extrayendo intención: {e}")
        return None
