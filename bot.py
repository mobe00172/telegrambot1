import os
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
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

print(f"Bot startet mit Token: {TOKEN[:5]}...")
print(f"Chat-ID: {CHAT_ID}")

# Flask-App
app = Flask(__name__)

# Telegram Bot
bot = Bot(token=TOKEN)

# Zustände für ConversationHandler
WAITING_FOR_CATEGORY, WAITING_FOR_TASK, WAITING_FOR_DELETE_TASK = range(3)

# Routes
@app.route("/")
def index():
    return "Telegram Bot is running!"

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    print("Webhook wurde aufgerufen!")
    if request.method == "POST":
        print("POST-Anfrage erhalten")
        update = Update.de_json(request.get_json(), bot)
        
        if update.message:
            chat_id = update.message.chat.id
            text = update.message.text
            
            # Befehlsverarbeitung
            if text == "/start":
                bot.send_message(
                    chat_id=chat_id,
                    text="Hallo! Ich bin dein Telegram-Bot 🚀\n"
                         "Verfügbare Befehle:\n"
                         "/start - Bot starten\n"
                         "/help - Hilfe anzeigen\n"
                         "/addtask - Aufgabe hinzufügen\n"
                         "/showtasks - Aufgaben anzeigen\n"
                         "/deletetask - Aufgabe löschen"
                )
            
            elif text == "/help":
                bot.send_message(
                    chat_id=chat_id,
                    text="Du kannst folgende Befehle verwenden:\n"
                         "/start - Bot starten\n"
                         "/help - Hilfe anzeigen\n"
                         "/addtask - Aufgabe hinzufügen\n"
                         "/showtasks - Aufgaben anzeigen\n"
                         "/deletetask - Aufgabe löschen"
                )
            
            elif text == "/addtask":
                bot.send_message(
                    chat_id=chat_id,
                    text="Bitte gib die Kategorie für die neue Aufgabe ein:",
                    reply_markup=ReplyKeyboardMarkup([['Arbeit', 'Privat']], one_time_keyboard=True)
                )
                return "OK", 200
            
            elif text == "/showtasks":
                try:
                    with open("daily_goals.txt", "r") as file:
                        tasks = file.readlines()
                    if tasks:
                        bot.send_message(chat_id=chat_id, text="Deine Aufgaben:\n" + ''.join(tasks))
                    else:
                        bot.send_message(chat_id=chat_id, text="Keine Aufgaben vorhanden.")
                except FileNotFoundError:
                    bot.send_message(chat_id=chat_id, text="Keine Aufgaben vorhanden.")
            
            elif text == "/deletetask":
                try:
                    with open("daily_goals.txt", "r") as file:
                        tasks = file.readlines()
                    if tasks:
                        task_message = "Wähle die Nummer der Aufgabe zum Löschen:\n"
                        for i, task in enumerate(tasks, 1):
                            task_message += f"{i}. {task}"
                        bot.send_message(chat_id=chat_id, text=task_message)
                    else:
                        bot.send_message(chat_id=chat_id, text="Keine Aufgaben zum Löschen vorhanden.")
                except FileNotFoundError:
                    bot.send_message(chat_id=chat_id, text="Keine Aufgaben zum Löschen vorhanden.")
            
            # Normale Nachrichtenverarbeitung
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=f"Ich habe deine Nachricht erhalten: {text}"
                )
        
        return "OK", 200
    return "OK", 200

# Tägliche Aufgaben senden
def send_daily_tasks():
    print("Sende tägliche Aufgaben...")
    file_name = "daily_goals.txt"
    try:
        with open(file_name, "r") as file:
            tasks = file.readlines()
        if tasks:
            bot.send_message(chat_id=CHAT_ID, text="Heutige Aufgaben:\n" + ''.join(tasks))
        else:
            bot.send_message(chat_id=CHAT_ID, text="Keine täglichen Aufgaben für heute.")
    except FileNotFoundError:
        bot.send_message(chat_id=CHAT_ID, text="Keine täglichen Aufgaben für heute.")

if __name__ == "__main__":
    print("Bot-Konfiguration startet...")
    
    # Scheduler einrichten
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_tasks, "cron", hour=6, minute=0)
    scheduler.start()
    print("Scheduler läuft...")

    # Webhook setzen
    webhook_url = f"https://telegrambot1-3.onrender.com/webhook/{TOKEN}"
    bot.set_webhook(webhook_url)
    print(f"Webhook gesetzt auf: {webhook_url}")

    # Server starten
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
