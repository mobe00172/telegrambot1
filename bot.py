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

# Token Konfiguration
TOKEN = "7743077318:AAEZw-EUa0A4kL65wjkjbnI-37nA6UsH8k0"
CHAT_ID = 7743077318

print(f"DEBUG: Verwende Bot-Token: {TOKEN[:5]}...")
print(f"DEBUG: Verwende Chat-ID: {CHAT_ID}")

# Telegram Application
application = Application.builder().token(TOKEN).build()

# Zustände für ConversationHandler
WAITING_FOR_CATEGORY, WAITING_FOR_TASK, WAITING_FOR_DELETE_TASK = range(3)

# Flask-App
app = Flask(__name__)

# Webhook Route für Telegram
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
async def webhook():
    if request.method == "POST":
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        await application.update_queue.put(update)
        return "OK", 200
    return "OK", 200

# Basis-Route für Healthcheck
@app.route("/")
def index():
    return "Telegram Bot is running!"

# Tägliche Aufgaben senden
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

# Start Command
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

# Help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Du kannst folgende Befehle verwenden:\n"
        "/start - Bot starten\n"
        "/help - Hilfe anzeigen\n"
        "/addtask - Aufgabe hinzufügen\n"
        "/showtasks - Aufgaben anzeigen\n"
        "/deletetask - Aufgabe löschen"
    )

# Add Task Command
async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bitte gib die Kategorie für die neue Aufgabe ein:",
        reply_markup=ReplyKeyboardMarkup([['Arbeit', 'Privat']], one_time_keyboard=True)
    )
    return WAITING_FOR_CATEGORY

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await update.message.reply_text(
        "Bitte gib die Aufgabe ein:",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_FOR_TASK

async def confirm_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = context.user_data.get('category', 'Allgemein')
    task = update.message.text
    with open("daily_goals.txt", "a") as file:
        file.write(f"[{category}] {task}\n")
    await update.message.reply_text(f"Aufgabe zur Kategorie {category} hinzugefügt!")
    return ConversationHandler.END

# Show Tasks Command
async def showtasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("daily_goals.txt", "r") as file:
            tasks = file.readlines()
        if tasks:
            await update.message.reply_text("Deine Aufgaben:\n" + ''.join(tasks))
        else:
            await update.message.reply_text("Keine Aufgaben vorhanden.")
    except FileNotFoundError:
        await update.message.reply_text("Keine Aufgaben vorhanden.")
    return ConversationHandler.END

# Delete Task Command
async def deletetask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("daily_goals.txt", "r") as file:
            tasks = file.readlines()
        if tasks:
            context.user_data['tasks'] = tasks
            task_message = "Wähle die Nummer der Aufgabe zum Löschen:\n"
            for i, task in enumerate(tasks, 1):
                task_message += f"{i}. {task}"
            await update.message.reply_text(task_message)
            return WAITING_FOR_DELETE_TASK
        else:
            await update.message.reply_text("Keine Aufgaben zum Löschen vorhanden.")
            return ConversationHandler.END
    except FileNotFoundError:
        await update.message.reply_text("Keine Aufgaben zum Löschen vorhanden.")
        return ConversationHandler.END

async def confirm_delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        task_num = int(update.message.text) - 1
        tasks = context.user_data.get('tasks', [])
        if 0 <= task_num < len(tasks):
            deleted_task = tasks.pop(task_num)
            with open("daily_goals.txt", "w") as file:
                file.writelines(tasks)
            await update.message.reply_text(f"Aufgabe gelöscht: {deleted_task}")
        else:
            await update.message.reply_text("Ungültige Aufgabennummer.")
    except (ValueError, IndexError):
        await update.message.reply_text("Bitte gib eine gültige Nummer ein.")
    return ConversationHandler.END

if __name__ == "__main__":
    print("DEBUG: Bot-Konfiguration startet...")
    
    # Scheduler einrichten
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_tasks, "cron", hour=6, minute=0, args=[application])
    scheduler.start()
    print("DEBUG: Scheduler läuft...")

    # Conversation Handler konfigurieren
    conv_handler_add = ConversationHandler(
        entry_points=[CommandHandler("addtask", addtask)],
        states={
            WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_task)],
            WAITING_FOR_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_task)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    conv_handler_delete = ConversationHandler(
        entry_points=[CommandHandler("deletetask", deletetask)],
        states={
            WAITING_FOR_DELETE_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_task)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    # Handler hinzufügen
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("showtasks", showtasks))
    application.add_handler(conv_handler_add)
    application.add_handler(conv_handler_delete)

    # Webhook setzen
    webhook_url = f"https://telegrambot1-3.onrender.com/webhook/{TOKEN}"
    application.bot.set_webhook(url=webhook_url)
    print(f"DEBUG: Webhook gesetzt auf: {webhook_url}")

    # Server starten
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
