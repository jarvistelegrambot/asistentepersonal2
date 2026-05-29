import json
import os
import datetime

VEHICLE_FILE = "vehicle.json"

def get_vehicle_data():
    """Devuelve los datos actuales del vehículo."""
    if not os.path.exists(VEHICLE_FILE):
        return {
            "itv_date": None,
            "maintenance_date": None,
            "tax_date": None
        }
    try:
        with open(VEHICLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "itv_date": None,
            "maintenance_date": None,
            "tax_date": None
        }

def save_vehicle_data(data):
    with open(VEHICLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def renew_event(event_type):
    """
    event_type debe ser 'itv', 'maintenance', o 'tax'.
    Se renueva sumando 365 días a la fecha actual.
    """
    data = get_vehicle_data()
    next_year = datetime.datetime.now() + datetime.timedelta(days=365)
    key = f"{event_type}_date"
    data[key] = next_year.strftime("%Y-%m-%d")
    save_vehicle_data(data)
    return data[key]

def get_upcoming_warnings():
    """
    Devuelve avisos para eventos que caducan en 15, 7 o 1 días.
    """
    data = get_vehicle_data()
    now = datetime.datetime.now()
    warnings = []
    
    thresholds = [15, 7, 1]
    
    event_names = {
        "itv": "la ITV",
        "maintenance": "la revisión/mantenimiento",
        "tax": "el impuesto de circulación"
    }
    
    for event_type, name in event_names.items():
        date_str = data.get(f"{event_type}_date")
        if not date_str:
            continue
            
        try:
            event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            delta = (event_date.date() - now.date()).days
            
            if delta in thresholds:
                warnings.append({
                    "event": name,
                    "days_left": delta,
                    "date": date_str
                })
        except:
            pass
            
    return warnings
