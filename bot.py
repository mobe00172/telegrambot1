import os
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# -----------------------------------------
# Fest kodierte Tokens
# -----------------------------------------
TOKEN = "7743077318:AAEZw-EUa0A4kL65wjkjbnI-37nA6UsH8k0"
CHAT_ID = 7743077318

print(f"DEBUG: Verwende Bot-Token: {TOKEN[:5]}...")
print(f"DEBUG: Verwende Chat-ID: {CHAT_ID}")

# Telegram Application bauen (Webhook statt Polling)
application = Application.builder().token(TOKEN).build()

# Zustände für ConversationHandler
WAITING_FOR_CATEGORY, WAITING_FOR_TASK, WAITING_FOR_DELETE_TASK = range(3)

# Flask-App für Webhook
app = Flask(__name__)

@app.route("/")
def index():
    return "Hallo, dein Telegram-Web-Bot läuft (Flask und Werkzeug korrekt konfiguriert)."

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
async def receive_update():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    await application.update_queue.put(update)
    return "OK", 200

# Automatische Nachricht um 6:00 Uhr
async def send_daily_tasks(context: ContextTypes.DEFAULT_TYPE):
    file_name = "daily_goals.txt"
    try:
        with open(file_name, "r") as file:
            tasks = file.readlines()
        if tasks:
            await context.bot.send_message(chat_id=CHAT_ID, text="Heutige Aufgaben:\n" + ''.join(tasks))
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text="Keine täglichen Aufgaben für heute.")
    except FileNotFoundError:
        await context.bot.send_message(chat_id=CHAT_ID, text="Keine täglichen Aufgaben für heute.")

# /start-Befehl
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hallo! Ich bin dein Telegram-Bot 🚀\n"
        "Verfügbare Befehle:\n"
        "/start - Bot starten\n"
        "/help - Hilfe anzeigen\n"
        "/addtask - Aufgabe hinzufügen\n"
        "/showtasks - Aufgaben anzeigen\n"
        "/deletetask - Aufgabe löschen"
    )

# /help-Befehl
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Du kannst folgende Befehle verwenden:\n"
        "/start - Bot starten\n"
        "/help - Hilfe anzeigen\n"
        "/addtask - Aufgabe hinzufügen\n"
        "/showtasks - Aufgaben anzeigen\n"
        "/deletetask - Aufgabe löschen"
    )

# Füge hier die restlichen Befehlsfunktionen wie /addtask, /showtasks usw. hinzu
# (identisch mit dem ursprünglichen Code)

# -----------------------------------------
# Bot-Konfiguration und Scheduler im Hauptblock
# -----------------------------------------
if __name__ == "__main__":
    print("DEBUG: Bot-Konfiguration startet...")
    
    # Scheduler für tägliche Aufgaben einrichten
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_tasks, "cron", hour=6, minute=0, args=[application.bot])
    scheduler.start()
    print("DEBUG: Scheduler läuft...")

    # Conversation Handler definieren
    conv_handler_add = ConversationHandler(
        entry_points=[CommandHandler("addtask", addtask)],
        states={
            WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_task)],
            WAITING_FOR_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_task)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    conv_handler_show = ConversationHandler(
        entry_points=[CommandHandler("showtasks", showtasks)],
        states={
            WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, display_tasks)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    conv_handler_delete = ConversationHandler(
        entry_points=[CommandHandler("deletetask", deletetask)],
        states={
            WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_task_to_delete)],
            WAITING_FOR_DELETE_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_task)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    # Handler zur App hinzufügen
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler_add)
    application.add_handler(conv_handler_show)
    application.add_handler(conv_handler_delete)

    # Webhook setzen (Render-URL anpassen!)
    render_url = os.getenv("RENDER_EXTERNAL_URL", "https://DEINERENDERURL.onrender.com")
    webhook_url = f"{render_url}/webhook/{TOKEN}"
    application.bot.set_webhook(url=webhook_url)
    print(f"DEBUG: Webhook gesetzt auf: {webhook_url}")

    # Flask-App starten
    app.run(debug=True, port=5000)
