import schedule
import time
import asyncio
from telegram import Bot
import config
from services import calendar_service, news_service, weather_traffic_service, finance_service, todo_service, subscription_service, vehicle_service

def generate_morning_message():
    """Compila el texto del mensaje matutino."""
    message = f"🌅 *¡Buenos días {config.USER_NAME}!* Aquí tienes tu resumen para arrancar el día:\n\n"
    
    # 2. Mercados Financieros
    market_info = finance_service.get_market_data()
    message += f"{market_info}\n\n"
    
    # 3. Clima y Tráfico
    wt_info = weather_traffic_service.get_weather_and_traffic()
    message += f"{wt_info}\n\n"
    
    # 4. Noticias
    news_info = news_service.get_top_financial_news()
    message += f"{news_info}\n\n"
    
    # 5. Agenda (Hoy y resto de semana)
    today_events = calendar_service.get_today_events()
    agenda_info = calendar_service.format_events(today_events, title="📅 *Tu agenda para hoy:*")
    message += f"{agenda_info}\n\n"
    
    week_events = calendar_service.get_week_events()
    # Filtrar los eventos que ya salieron hoy
    today_ids = {e['id'] for e in today_events}
    future_events = [e for e in week_events if e['id'] not in today_ids]
    
    if future_events:
        agenda_week = calendar_service.format_events(future_events, title="📅 *Eventos para el resto de la semana:*")
        message += f"{agenda_week}\n\n"
        
    # 6. Tareas Pendientes
    todos = todo_service.get_todos()
    pending_todos = [t for t in todos if not t["completed"]]
    if pending_todos:
        message += f"📝 *Tienes {len(pending_todos)} tareas pendientes.*\n👉 Haz clic en /tareas para verlas y tacharlas.\n\n"
    else:
        message += f"📝 *No tienes tareas pendientes.*\n👉 Haz clic en /tareas para gestionar tu lista.\n\n"
        
    # 7. Suscripciones Próximas
    upcoming_subs = subscription_service.get_upcoming_charges(days_ahead=2)
    if upcoming_subs:
        message += "🚨 *¡Aviso de cobros próximos!*\n"
        for s in upcoming_subs:
            message += f"- En 2 días te cobrarán *{s['cost']:.2f} €* de _{s['name']}_.\n"
        message += "👉 Revisa tus /suscripciones si deseas cancelarlo.\n\n"
        
    # 8. Alertas de Vehículo
    vehicle_warnings = vehicle_service.get_upcoming_warnings()
    if vehicle_warnings:
        message += "🚘 *¡Alertas de tu Coche!*\n"
        for w in vehicle_warnings:
            if w['days_left'] == 1:
                time_str = "*MAÑANA*"
            else:
                time_str = f"en *{w['days_left']} días*"
            message += f"⚠️ Te caduca {w['event']} {time_str} ({w['date']}).\n"
        message += "👉 Avísame cuando lo renueves para que actualice la fecha.\n"
        
    return message

def send_morning_message():
    """Compila y envía el mensaje matutino."""
    if not config.USER_CHAT_ID or config.USER_CHAT_ID == "tu_chat_id_de_telegram":
        print("Error: USER_CHAT_ID no configurado. No se puede enviar el mensaje matutino.")
        return

    print("Ejecutando tarea de mensaje matutino...")
    message = generate_morning_message()
    
    # Enviar mensaje usando el bot
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    
    # schedule se ejecuta sincrónicamente, pero telegram python bot v20+ es async.
    # Necesitamos crear un loop de eventos para enviar el mensaje.
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(bot.send_message(chat_id=config.USER_CHAT_ID, text=message, parse_mode='Markdown'))
    print("Mensaje matutino enviado con éxito.")

def start_scheduler():
    """Inicia el scheduler que ejecuta la tarea todos los días a las 09:00 AM."""
    schedule.every().day.at("09:00", "Europe/Madrid").do(send_morning_message)
    
    print("Scheduler iniciado. Esperando para ejecutar tareas...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
