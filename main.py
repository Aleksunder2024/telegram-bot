import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Получаем токен из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан. Проверь переменные окружения в Railway!")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот aleksandraibot33 🚀\n"
        "Я могу присылать тебе челленджи и интересные статьи!"
    )

# Создаем приложение бота
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Добавляем обработчик команды /start
app.add_handler(CommandHandler("start", start))

# Запускаем бота
print("Бот запущен...")
app.run_polling()
