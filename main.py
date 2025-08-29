import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

# Получаем токен из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан. Проверь переменные окружения в Railway!")

# Создаём объект бота
bot = Bot(token=TELEGRAM_TOKEN)
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет! Я бот aleksandraibot33 🚀\n"
        "Я могу присылать тебе челленджи и интересные статьи!"
    )

# Добавляем обработчик команды /start
dispatcher.add_handler(CommandHandler("start", start))

# Запускаем бота
print("Бот запущен...")
updater.start_polling()
updater.idle()
