# Telegram Challenge Bot

Бот с ИИ-ассистентом, который предлагает ежедневные челленджи в разных категориях и отвечает на вопросы.

## Функции

- Ответы на вопросы с помощью Google Gemini AI
- Персонализированные челленджи в разных категориях
- Проверка кода и поиск ошибок
- Создание программ тренировок
- Запоминание контекста общения и сложности заданий

## Требования

- Python 3.8+
- python-telegram-bot
- google-generativeai
- requests

## Настройка

1. Создайте бота через @BotFather в Telegram и получите токен
2. Получите API ключ Google Gemini на https://aistudio.google.com/
3. Установите переменные окружения:
   - TELEGRAM_API_TOKEN: токен вашего бота
   - GOOGLE_API_KEY: ваш API ключ Google Gemini

## Запуск локально

```bash
pip install -r requirements.txt
python challenge_bot.py