import logging
import tempfile
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

import config
from services import calendar_service, nlp_service, todo_service, subscription_service, vehicle_service
from scheduler import generate_morning_message

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def post_init(application):
    """Configura el menú del bot en Telegram."""
    await application.bot.set_my_commands([
        BotCommand("start", "Iniciar el bot y ver bienvenida"),
        BotCommand("hoy", "Ver tu agenda de hoy"),
        BotCommand("semana", "Ver tu agenda de los próximos 7 días"),
        BotCommand("tareas", "Ver tu lista interactiva de tareas pendientes"),
        BotCommand("resumen", "Ver tu reporte diario completo ahora mismo"),
        BotCommand("suscripciones", "Ver y gestionar tus suscripciones mensuales"),
        BotCommand("coche", "Ver estado y fechas clave de tu vehículo")
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /start"""
    chat_id = update.effective_chat.id
    welcome_text = (
        f"¡Hola! Soy tu asistente personal.\n"
        f"Tu Chat ID es: `{chat_id}`\n"
        f"Por favor, pon este Chat ID en tu archivo .env (USER_CHAT_ID={chat_id}) "
        f"para que pueda enviarte los mensajes matutinos de las 09:00 AM.\n\n"
        f"Puedes decirme comandos como /hoy o /semana para ver tu agenda.\n"
        f"También puedes enviarme un mensaje de texto o voz pidiéndome que agende algo."
    )
    await context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode='Markdown')

async def agenda_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /hoy"""
    events = calendar_service.get_today_events()
    response = calendar_service.format_events(events, title="📅 *Eventos de hoy:*")
    await update.message.reply_text(response, parse_mode='Markdown')

async def agenda_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /semana"""
    events = calendar_service.get_week_events()
    response = calendar_service.format_events(events, title="📅 *Eventos de los próximos 7 días:*")
    await update.message.reply_text(response, parse_mode='Markdown')

async def resumen_matutino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /resumen"""
    status_msg = await update.message.reply_text("⏳ Recopilando tu resumen diario, dame unos segundos...")
    message = generate_morning_message()
    await status_msg.edit_text(message, parse_mode='Markdown')

async def agenda_tareas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /tareas"""
    reply_markup = get_todo_keyboard()
    await update.message.reply_text("📝 *Tus Tareas Pendientes*", reply_markup=reply_markup, parse_mode='Markdown')

async def gestion_suscripciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /suscripciones"""
    subs = subscription_service.get_subs()
    if not subs:
        msg = "💳 *Control de Suscripciones*\n\nNo tienes ninguna suscripción registrada."
    else:
        total = sum(s['cost'] for s in subs)
        msg = f"💳 *Control de Suscripciones*\n\nTotal mensual: *{total:.2f} €*\n\nTus suscripciones:"
    await update.message.reply_text(msg, reply_markup=get_sub_keyboard(), parse_mode='Markdown')

def get_sub_keyboard():
    subs = subscription_service.get_subs()
    keyboard = []
    for s in subs:
        keyboard.append([InlineKeyboardButton(f"🗑️ {s['name']} ({s['cost']}€ - Día {s['day']})", callback_data=f"sub_del_{s['id']}")])
    if keyboard:
        return InlineKeyboardMarkup(keyboard)
    return None

async def estado_coche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /coche"""
    data = vehicle_service.get_vehicle_data()
    
    def format_date(date_str):
        if not date_str:
            return "Desconocido (Dime cuándo lo renuevas)"
        return date_str
        
    msg = (
        "🚘 *Asistente de Vehículo*\n\n"
        f"🛠️ *Próxima ITV:* {format_date(data['itv_date'])}\n"
        f"🔧 *Mantenimiento:* {format_date(data['maintenance_date'])}\n"
        f"📄 *Impuesto Circulación:* {format_date(data['tax_date'])}\n\n"
        "_💡 Tip: Envíame un audio diciendo 'He pasado la ITV hoy' y lo renovaré 1 año automáticamente._"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

def get_todo_keyboard():
    """Genera los botones interactivos de las tareas."""
    todos = todo_service.get_todos()
    keyboard = []
    
    for t in todos:
        icon = "✅" if t["completed"] else "❌"
        keyboard.append([InlineKeyboardButton(f"{icon} {t['text']}", callback_data=f"todo_toggle_{t['id']}")])
        
    keyboard.append([
        InlineKeyboardButton("🗑️ Borrar Completadas", callback_data="todo_clear")
    ])
    return InlineKeyboardMarkup(keyboard)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para los clics en los botones interactivos."""
    query = update.callback_query
    
    # Capa de seguridad extra: verificar que quien pulsa el botón es el dueño
    if str(query.from_user.id) != str(config.USER_CHAT_ID):
        await query.answer("⛔ Acceso denegado.", show_alert=True)
        return
        
    await query.answer()
    
    data = query.data
    if data.startswith("todo_toggle_"):
        todo_id = data.split("todo_toggle_")[1]
        todo_service.toggle_todo(todo_id)
        await query.edit_message_reply_markup(reply_markup=get_todo_keyboard())
        
    elif data == "todo_clear":
        todo_service.clear_completed()
        await query.edit_message_reply_markup(reply_markup=get_todo_keyboard())
        
    elif data.startswith("sub_del_"):
        sub_id = data.split("sub_del_")[1]
        subscription_service.delete_sub(sub_id)
        
        subs = subscription_service.get_subs()
        if not subs:
            msg = "💳 *Control de Suscripciones*\n\nNo tienes ninguna suscripción registrada."
        else:
            total = sum(s['cost'] for s in subs)
            msg = f"💳 *Control de Suscripciones*\n\nTotal mensual: *{total:.2f} €*\n\nTus suscripciones:"
            
        await query.edit_message_text(text=msg, reply_markup=get_sub_keyboard(), parse_mode='Markdown')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador de mensajes de texto (para crear eventos)"""
    text = update.message.text
    await process_intent(text, update)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador de mensajes de voz"""
    voice = update.message.voice
    file_id = voice.file_id
    
    status_message = await update.message.reply_text("🎙️ Procesando audio...")
    
    try:
        new_file = await context.bot.get_file(file_id)
        
        # Guardar temporalmente como .ogg
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio:
            temp_path = temp_audio.name
            
        await new_file.download_to_drive(temp_path)
        
        # Transcribir con OpenAI Whisper
        transcription = nlp_service.transcribe_audio(temp_path)
        
        # Eliminar archivo temporal
        os.remove(temp_path)
        
        if transcription.startswith("Error"):
            await status_message.edit_text(transcription)
            return
            
        await status_message.edit_text(f"📝 *Transcripción:* {transcription}", parse_mode='Markdown')
        
        # Procesar intención sobre el texto transcrito
        await process_intent(transcription, update)
        
    except Exception as e:
        await status_message.edit_text(f"❌ Error al procesar el audio: {e}")

async def process_intent(text, update: Update):
    """Procesa el texto para ver si se debe crear un evento o tarea."""
    intent = nlp_service.extract_event_intent(text)
    
    is_event = intent and (intent.get('intent') == 'create_event' or 'summary' in intent)
    is_todo = intent and intent.get('intent') == 'add_todo'
    is_sub = intent and intent.get('intent') == 'add_subscription'
    is_vehicle = intent and intent.get('intent') == 'update_vehicle'
    
    if is_event:
        summary = intent.get('summary')
        start = intent.get('start_time_iso')
        end = intent.get('end_time_iso')
        
        msg = f"⏳ Agendando: *{summary}*..."
        status_msg = await update.message.reply_text(msg, parse_mode='Markdown')
        
        result = calendar_service.create_event(summary, start, end)
        await status_msg.edit_text(result, parse_mode='Markdown')
        
    elif is_todo:
        task_text = intent.get('task')
        todo_service.add_todo(task_text)
        await update.message.reply_text(f"✅ Añadido a tareas: *{task_text}*\nEscribe /tareas para ver tu lista.", parse_mode='Markdown')
        
    elif is_sub:
        sub_name = intent.get('sub_name')
        sub_cost = intent.get('sub_cost')
        sub_day = intent.get('sub_day')
        
        if sub_cost is None or sub_day is None:
            await update.message.reply_text(f"⚠️ Me has pedido añadir la suscripción de *{sub_name}*, pero me falta información.\n\nPor favor, dímelo todo junto. Por ejemplo: _'Añade la suscripción de {sub_name} que cuesta 10 euros y me lo cobran los días 5'_.", parse_mode='Markdown')
        else:
            subscription_service.add_sub(sub_name, sub_cost, sub_day)
            await update.message.reply_text(f"💳 ¡Suscripción a *{sub_name}* ({sub_cost}€/mes) añadida!\nTe avisaré 2 días antes de cada día {sub_day}.", parse_mode='Markdown')
            
    elif is_vehicle:
        event_type = intent.get('vehicle_event')
        new_date = vehicle_service.renew_event(event_type)
        nombres = {"itv": "ITV", "maintenance": "Mantenimiento", "tax": "Impuesto de Circulación"}
        nombre = nombres.get(event_type, event_type)
        await update.message.reply_text(f"🚘 ¡Anotado! He renovado *{nombre}*.\nLa próxima fecha clave será el: *{new_date}*.", parse_mode='Markdown')
        
    else:
        await update.message.reply_text("No entendí muy bien. Intenta ser más específico.")

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_dummy_server():
    port = int(os.environ.get("PORT", 7860))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    print(f"Servidor web fantasma escuchando en el puerto {port}")
    server.serve_forever()

if __name__ == '__main__':
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "tu_token_de_telegram":
        print("Error: TELEGRAM_BOT_TOKEN no está configurado.")
        exit(1)
        
    # 1. Iniciar servidor web fantasma en hilo separado (Para Render)
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # 2. Iniciar el planificador matutino en hilo separado
    from scheduler import start_scheduler
    threading.Thread(target=start_scheduler, daemon=True).start()
        
    # 3. Iniciar el bot de Telegram con más tiempo de espera (para evitar bloqueos en la nube)
    application = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )
    
    application.add_handler(CommandHandler('start', start))
    
    # Filtro de seguridad para que el bot SOLO te responda a ti
    try:
        user_id = int(config.USER_CHAT_ID)
        auth_filter = filters.Chat(chat_id=user_id)
    except (TypeError, ValueError):
        print("⚠️ CUIDADO: USER_CHAT_ID no válido. El bot responderá a cualquiera.")
        auth_filter = filters.ALL
        
    application.add_handler(CommandHandler('hoy', agenda_hoy, filters=auth_filter))
    application.add_handler(CommandHandler('semana', agenda_semana, filters=auth_filter))
    application.add_handler(CommandHandler('tareas', agenda_tareas, filters=auth_filter))
    application.add_handler(CommandHandler('suscripciones', gestion_suscripciones, filters=auth_filter))
    application.add_handler(CommandHandler('coche', estado_coche, filters=auth_filter))
    application.add_handler(CommandHandler('resumen', resumen_matutino, filters=auth_filter))
    
    # Callbacks (botones) no necesitan filtro explícito en el handler si los botones solo se generan tras un comando autorizado, 
    # pero es buena práctica protegerlos en la propia función si fuera necesario.
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Handlers para texto y voz
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND) & auth_filter, handle_text))
    application.add_handler(MessageHandler(filters.VOICE & auth_filter, handle_voice))
    
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling()
