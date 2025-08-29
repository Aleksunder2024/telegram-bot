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

# ====== Пример статей ======
articles = {
    "спорт": ["https://habr.com/ru/articles/123456/"],
    "книги": ["https://example.com/fantasy-world"],
    "крипта": ["https://example.com/crypto101"]
}

# ====== Сохранение данных ======
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"user_data": user_data, "articles": articles}, f, ensure_ascii=False, indent=2)

# ====== Динамические шаблоны для fallback ======
templates = {
    "спорт": ["Сделай {n} приседаний", "Пройди {n} шагов", "Планка {n} секунд"],
    "книги": ["Прочитай {n} страниц", "Выбери новую книгу жанра {genre}"],
    "крипта": ["Прочитай статью про {coin}", "Посмотри видео о {topic}"]
}

def fallback_challenge(category: str):
    if category not in templates:
        return "Сделай что-то полезное!"
    template = random.choice(templates[category])
    n = random.randint(5, 20)
    genre = random.choice(["фэнтези", "научную фантастику", "классическую литературу"])
    coin = random.choice(["BTC", "ETH", "ADA"])
    topic = random.choice(["DeFi", "NFT", "стейкинг"])
    return template.format(n=n, genre=genre, coin=coin, topic=topic)

# ====== Генерация задания через HF API ======
def generate_challenge(category: str) -> str:
    url = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-1.3B"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    prompt = f"Придумай короткое мотивирующее ежедневное задание для категории '{category}':"
    try:
        response = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=10)
        if response.status_code == 200:
            text = response.json()[0].get('generated_text', '').strip()
            if text:
                return text
        # Если API не ответил корректно
        return fallback_challenge(category)
    except Exception:
        return fallback_challenge(category)

# ====== Ассистент для произвольных вопросов ======
def generate_assistant_hint(user_text: str) -> str:
    url = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-1.3B"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    prompt = (
        f"Ты ассистент для Telegram-бота, который генерирует челленджи. "
        f"Пользователь пишет: '{user_text}'. "
        f"Объясни, что можно сделать, или как пользоваться ботом. "
        f"Дай понятную короткую подсказку."
    )
    try:
        response = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=10)
        if response.status_code == 200:
            text = response.json()[0].get("generated_text", "").strip()
            if text:
                return text
        return "Прости, я пока не могу подсказать. Попробуй уточнить вопрос или использовать команды /help."
    except Exception:
        return "Прости, я пока не могу подсказать. Попробуй уточнить вопрос или использовать команды /help."

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

# ====== Обработка сообщений ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    text = update.message.text.lower()
    categories = list(user_data[chat_id]["completed"].keys())

    # Если совпадает с категорией — выдаём челлендж
    if text in categories:
        challenge = generate_challenge(text)
        await update.message.reply_text(f"Челлендж ({text}): {challenge}")
    else:
        # Используем ассистента для подсказки
        hint = generate_assistant_hint(text)
        await update.message.reply_text(hint)

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
