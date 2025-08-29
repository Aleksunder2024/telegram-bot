import os
import random
import json
import requests
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ====== Telegram ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")  # Hugging Face API token
DATA_FILE = "user_data.json"

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан!")

if not HF_API_TOKEN:
    raise ValueError("HF_API_TOKEN не задан!")

# ====== Загрузка данных ======
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        user_data = json.load(f)
else:
    user_data = {}

# ====== Список статей ======
articles = {
    "спорт": ["https://habr.com/ru/articles/123456/"],
    "книги": ["https://example.com/fantasy-world"],
    "крипта": ["https://example.com/crypto101"]
}

# ====== Сохраняем данные ======
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"user_data": user_data, "articles": articles}, f, ensure_ascii=False, indent=2)

# ====== Генерация задания через Hugging Face Inference API ======
def generate_challenge(category: str) -> str:
    url = "https://api-inference.huggingface.co/models/gpt2"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    prompt = f"Придумай короткое и мотивирующее ежедневное задание для категории '{category}':"
    response = requests.post(url, headers=headers, json={"inputs": prompt})
    try:
        text = response.json()[0]['generated_text']
        return text.strip()
    except Exception:
        return f"Задание для '{category}' не получилось сгенерировать."

# ====== Команды ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id not in user_data:
        user_data[chat_id] = {"completed": {}, "notify_hour": 10, "daily_count": 2}
        save_data()
    await update.message.reply_text(
        "Привет! Я бот, который генерирует ежедневные челленджи 🎯"
    )

async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Используй /add_category название_категории")
        return
    category = context.args[0].lower()
    for chat_id in user_data:
        user_data[chat_id]["completed"].setdefault(category, [])
    save_data()
    await update.message.reply_text(f"Категория '{category}' добавлена!")

async def add_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Используй /add_challenge категория текст_задания")
        return
    category = context.args[0].lower()
    text = " ".join(context.args[1:])
    user_data.setdefault(str(update.message.chat_id), {"completed": {}})
    user_data[str(update.message.chat_id)]["completed"].setdefault(category, []).append(text)
    save_data()
    await update.message.reply_text(f"Задание добавлено в категорию '{category}'!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    text = update.message.text.lower()
    if chat_id not in user_data:
        user_data[chat_id] = {"completed": {}, "notify_hour": 10, "daily_count": 2}
        save_data()
    if text in user_data[chat_id]["completed"]:
        challenge = generate_challenge(text)
        user_data[chat_id]["completed"][text].append(challenge)
        save_data()
        article = random.choice(articles.get(text, [])) if articles.get(text) else "Нет статьи"
        await update.message.reply_text(f"Челлендж ({text}): {challenge}\nСтатья: {article}")
    else:
        await update.message.reply_text("Выберите существующую категорию или добавьте через /add_category")

# ====== Создаем бота ======
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add_category", add_category))
app.add_handler(CommandHandler("add_challenge", add_challenge))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ====== Запуск ======
if __name__ == "__main__":
    print("Бот запущен...")
    app.run_polling()
