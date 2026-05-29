import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config

# Scope para leer y escribir en Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Autentica y devuelve el servicio de Google Calendar."""
    creds = None
    
    # El archivo token.json almacena los tokens de acceso y refresco
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, SCOPES)
        
    # Si no hay credenciales válidas, solicita inicio de sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(config.CREDENTIALS_FILE):
                print(f"Error: No se encontró el archivo {config.CREDENTIALS_FILE}")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Guarda las credenciales para la próxima vez
        with open(config.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error construyendo el servicio de Calendar: {e}")
        return None

def get_events(time_min, time_max):
    """Obtiene los eventos entre dos fechas dadas."""
    service = get_calendar_service()
    if not service:
        return []
    
    events_result = service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

def get_today_events():
    """Obtiene los eventos del día de hoy."""
    now = datetime.datetime.utcnow()
    # Inicio del día (00:00 UTC, ajustar a hora local si es necesario)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    # Fin del día (23:59 UTC)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
    
    return get_events(start, end)

def get_week_events():
    """Obtiene los eventos de los próximos 7 días."""
    now = datetime.datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    end = (now + datetime.timedelta(days=7)).replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
    
    return get_events(start, end)

def format_events(events, title="Eventos:"):
    """Da formato a la lista de eventos para mostrarla en Telegram."""
    if not events:
        return f"{title}\nNo tienes eventos agendados."
    
    msg = f"{title}\n"
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        # Parse start time if it's dateTime to a readable format
        try:
            dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_time = start # Es un evento de todo el día (sólo fecha)
            
        msg += f"- {formatted_time}: {event['summary']}\n"
    return msg

def create_event(summary, start_time_iso, end_time_iso, description=""):
    """Crea un evento en el calendario."""
    service = get_calendar_service()
    if not service:
        return "Error de autenticación con Google Calendar."
    
    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time_iso,
            'timeZone': config.TIMEZONE,
        },
        'end': {
            'dateTime': end_time_iso,
            'timeZone': config.TIMEZONE,
        }
    }
    
    try:
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        return f"Evento creado exitosamente: {event.get('htmlLink')}"
    except Exception as e:
        print(f"Error creando evento: {e}")
        return f"Error al crear el evento: {e}"
