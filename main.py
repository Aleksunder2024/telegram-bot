import os
import asyncio
import random
import json
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ====== Hugging Face ======
from transformers import pipeline

# Создаем генератор текста
generator = pipeline("text-generation", model="gpt2")  # бесплатная базовая модель

# ====== Telegram ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DATA_FILE = "user_data.json"

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан!")

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

# ====== Генерация задания ======
async def generate_challenge(category: str) -> str:
    prompt = f"Придумай короткое и мотивирующее ежедневное задание для категории '{category}'"
    try:
        challenge = generator(prompt, max_length=50, do_sample=True)[0]['generated_text']
        return challenge.strip()
    except Exception as e:
        return f"Ошибка при генерации: {e}"

# ====== Команды ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id not in user_data:
        user_data[chat_id] = {"completed": {}, "notify_hour": 10, "daily_count": 2}
        save_data()
    await update.message.reply_text(
        "Привет! Я бот, который генерирует ежедневные челленджи 🎯\n"
        "Добавляй категории /add_category и задания через генерацию или вручную."
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

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if len(context.args) != 1:
        await update.message.reply_text("Используй /time HH")
        return
    try:
        hour = int(context.args[0])
        if 0 <= hour <= 23:
            user_data[chat_id]["notify_hour"] = hour
            save_data()
            await update.message.reply_text(f"Время уведомлений установлено на {hour}:00")
        else:
            await update.message.reply_text("Часы должны быть от 0 до 23")
    except ValueError:
        await update.message.reply_text("Введите число от 0 до 23")

async def set_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if len(context.args) != 1:
        await update.message.reply_text("Используй /count число_заданий")
        return
    try:
        count = int(context.args[0])
        if 1 <= count <= 5:
            user_data[chat_id]["daily_count"] = count
            save_data()
            await update.message.reply_text(f"Количество ежедневных заданий: {count}")
        else:
            await update.message.reply_text("Можно выбрать от 1 до 5 заданий в день")
    except ValueError:
        await update.message.reply_text("Некорректное число")

# ====== Обработчик сообщений ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    text = update.message.text.lower()
    if chat_id not in user_data:
        user_data[chat_id] = {"completed": {}, "notify_hour": 10, "daily_count": 2}
        save_data()
    if text in user_data[chat_id]["completed"]:
        challenge = await generate_challenge(text)
        user_data[chat_id]["completed"][text].append(challenge)
        save_data()
        article = random.choice(articles.get(text, [])) if articles.get(text) else "Нет статьи"
        await update.message.reply_text(f"Челлендж ({text}): {challenge}\nСтатья: {article}")
    else:
        await update.message.reply_text("Выберите существующую категорию или добавьте через /add_category")

# ====== Ежедневные уведомления ======
async def daily_notifications(app):
    await asyncio.sleep(5)
    while True:
        now = datetime.now()
        for chat_id, data in user_data.items():
            target_hour = data.get("notify_hour", 10)
            next_run = datetime.combine(now.date(), time(target_hour, 0))
            if now.hour >= target_hour:
                next_run += timedelta(days=1)
            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)

            count = data.get("daily_count", 2)
            for _ in range(count):
                if not data["completed"]:
                    continue
                category = random.choice(list(data["completed"].keys()))
                challenge = await generate_challenge(category)
                data["completed"][category].append(challenge)
                save_data()
                article = random.choice(articles.get(category, [])) if articles.get(category) else "Нет статьи"
                await app.bot.send_message(chat_id=int(chat_id),
                                           text=f"Ежедневный челлендж ({category}): {challenge}\nСтатья: {article}")

# ====== Создаем бота ======
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add_category", add_category))
app.add_handler(CommandHandler("add_challenge", add_challenge))
app.add_handler(CommandHandler("time", set_time))
app.add_handler(CommandHandler("count", set_count))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ====== Запуск ======
async def main():
    asyncio.create_task(daily_notifications(app))
    print("Бот запущен...")
    await app.run_polling()

import asyncio
asyncio.run(main())
