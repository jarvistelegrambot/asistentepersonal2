import os
from dotenv import load_dotenv

load_dotenv()

# Reconstruir token.json en la nube de Hugging Face desde un Secreto
if os.getenv("GOOGLE_TOKEN_JSON") and not os.path.exists("token.json"):
    with open("token.json", "w") as f:
        f.write(os.getenv("GOOGLE_TOKEN_JSON"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip('"\'')
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip('"\'')
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "").strip('"\'')

USER_CHAT_ID = os.getenv("USER_CHAT_ID")
USER_NAME = os.getenv("USER_NAME", "Jefe").strip('"\'')
TIMEZONE = os.getenv("TIMEZONE", "Europe/Madrid").strip('"\'')
CITY_NAME = os.getenv("CITY_NAME", "Madrid").strip('"\'')
TRAFFIC_BBOX = os.getenv("TRAFFIC_BBOX", "40.250,-3.950,40.550,-3.450").strip('"\'')

# Paths para credenciales de Google
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
