import requests
import config

MADRID_LAT = 40.4168
MADRID_LON = -3.7038

def get_madrid_weather():
    """Obtiene el clima actual en la ciudad configurada usando wttr.in (sin límite de API)."""
    url = f"https://wttr.in/{config.CITY_NAME}?format=j1"
    
    try:
        headers = {'User-Agent': 'curl/7.68.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current = data["current_condition"][0]["temp_C"]
            max_temp = data["weather"][0]["maxtempC"]
            min_temp = data["weather"][0]["mintempC"]
            return f"🌤️ *Clima en {config.CITY_NAME}:*\nActualmente {current}°C (Máx: {max_temp}°C | Mín: {min_temp}°C)"
        else:
            return f"🌤️ Error al obtener clima. Status: {response.status_code}."
            
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return f"🌤️ Hubo un error al obtener el clima."

def get_madrid_traffic():
    """Obtiene un resumen de incidencias de tráfico en Madrid usando TomTom API."""
    if not config.TOMTOM_API_KEY or config.TOMTOM_API_KEY == "tu_api_key_de_tomtom":
        return "Tráfico: API Key de TomTom no configurada."

    # Bounding box configurado por el usuario
    bbox = config.TRAFFIC_BBOX
    url = f"https://api.tomtom.com/traffic/services/5/incidentDetails?key={config.TOMTOM_API_KEY}&bbox={bbox}&fields={'{incidents{properties{iconCategory,magnitudeOfDelay}}}'}&language=es-ES"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            incidents = data.get("incidents", [])
            if not incidents:
                return f"🚗 *Tráfico en {config.CITY_NAME}:*\nNo se reportan incidencias graves en tu zona."
            
            return f"🚗 *Tráfico en {config.CITY_NAME}:*\nActualmente hay {len(incidents)} incidencias reportadas en tu zona."
        elif response.status_code == 401 or response.status_code == 403:
            return f"🚗 *Tráfico en {config.CITY_NAME}:*\n⚠️ API Key de TomTom no configurada o inválida. Revisa tus variables en Render."
        else:
            return f"🚗 Error al obtener tráfico. Status: {response.status_code}."
            
    except Exception as e:
        print(f"Error fetching traffic: {e}")
        return f"🚗 Hubo un error al obtener el tráfico."

def get_weather_and_traffic():
    """Devuelve un string combinado de clima y tráfico."""
    weather = get_madrid_weather()
    traffic = get_madrid_traffic()
    return f"{weather}\n\n{traffic}"
