import os
import random
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ====== Токены ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")  # Hugging Face API token
DATA_FILE = "user_data.json"

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан!")
if not HF_API_TOKEN:
    raise ValueError("HF_API_TOKEN не задан!")

# ====== Данные пользователей ======
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

# ====== Сохранение данных ======
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"user_data": user_data, "articles": articles}, f, ensure_ascii=False, indent=2)

# ====== Генерация задания через Hugging Face ======
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
        "Привет! Я бот, который генерирует ежедневные челленджи 🎯\n"
        "Используй /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = [
        "/start — запустить бота",
        "/help — список команд",
        "/add_category <название> — добавить категорию",
        "/add_challenge <категория> <текст> — добавить задание",
        "/categories — показать существующие категории",
        "/choose_category — выбрать категорию через кнопки"
    ]
    await update.message.reply_text("\n".join(commands))

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
    chat_id = str(update.message.chat_id)
    user_data.setdefault(chat_id, {"completed": {}})
    user_data[chat_id]["completed"].setdefault(category, []).append(text)
    save_data()
    await update.message.reply_text(f"Задание добавлено в категорию '{category}'!")

async def list_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id not in user_data:
        user_data[chat_id] = {"completed": {}, "notify_hour": 10, "daily_count": 2}
    categories = list(user_data[chat_id]["completed"].keys())
    if not categories:
        await update.message.reply_text("Пока нет категорий. Добавьте через /add_category")
    else:
        await update.message.reply_text("Существующие категории:\n" + "\n".join(categories))

# ====== Выбор категории через кнопки ======
async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    categories = list(user_data[chat_id]["completed"].keys())
    if not categories:
        await update.message.reply_text("Нет категорий. Добавьте через /add_category")
        return
    buttons = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Выберите категорию:", reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data
    challenge = generate_challenge(category)
    await query.edit_message_text(f"Челлендж ({category}): {challenge}")

# ====== Обработка текстовых сообщений ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    text = update.message.text.lower()
    categories = list(user_data[chat_id]["completed"].keys())
    if text in categories:
        challenge = generate_challenge(text)
        await update.message.reply_text(f"Челлендж ({text}): {challenge}")
    else:
        if categories:
            await update.message.reply_text(
                "Не понято. Выберите категорию из существующих:\n" + "\n".join(categories)
            )
        else:
            await update.message.reply_text("Категорий пока нет. Добавьте через /add_category")

# ====== Создание бота ======
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("add_category", add_category))
app.add_handler(CommandHandler("add_challenge", add_challenge))
app.add_handler(CommandHandler("categories", list_categories))
app.add_handler(CommandHandler("choose_category", choose_category))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ====== Запуск ======
if __name__ == "__main__":
    print("Бот запущен...")
    app.run_polling()
