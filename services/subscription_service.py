import json
import os
import uuid
import datetime

SUBS_FILE = "subscriptions.json"

def get_subs():
    """Devuelve la lista actual de suscripciones."""
    if not os.path.exists(SUBS_FILE):
        return []
    try:
        with open(SUBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_subs(subs):
    """Guarda la lista de suscripciones en el archivo JSON."""
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)

def add_sub(name, cost, day):
    """Añade una nueva suscripción a la lista."""
    subs = get_subs()
    name_clean = name.replace('*', '').replace('_', ' ').replace('[', '').replace(']', '')
    sub = {
        "id": str(uuid.uuid4())[:8],
        "name": name_clean,
        "cost": float(cost),
        "day": int(day)
    }
    subs.append(sub)
    save_subs(subs)
    return sub

def delete_sub(sub_id):
    """Elimina una suscripción por ID."""
    subs = get_subs()
    subs = [s for s in subs if s["id"] != sub_id]
    save_subs(subs)

def get_upcoming_charges(days_ahead=2):
    """Devuelve las suscripciones cuyo día de cobro es en 'days_ahead' días."""
    subs = get_subs()
    now = datetime.datetime.now()
    target_date = now + datetime.timedelta(days=days_ahead)
    target_day = target_date.day
    
    upcoming = []
    for s in subs:
        if s["day"] == target_day:
            upcoming.append(s)
    return upcoming
