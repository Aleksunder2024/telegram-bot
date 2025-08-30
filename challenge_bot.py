import os
import json
import random
import datetime
import sqlite3
import logging
from typing import Dict, List, Optional, Union

# Для работы с Telegram
import telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Для работы с Google Gemini API
import google.generativeai as genai
import requests

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Жестко закодированные токены (временное решение)
TELEGRAM_API_TOKEN = "8416538451:AAEjOIDh_XskQ39xvvHkN7IGIqLmVijBAKI"
GOOGLE_API_KEY = "AIzaSyBpaN1rt50z-_SJGi1ZP8IBl-jHTOTf9Rg"

# Дополнительно используем переменные окружения, если они доступны
telegram_env = os.getenv("TELEGRAM_API_TOKEN")
google_env = os.getenv("GOOGLE_API_KEY")
if telegram_env:
    TELEGRAM_API_TOKEN = telegram_env
if google_env:
    GOOGLE_API_KEY = google_env

print(f"Используется токен Telegram длиной: {len(TELEGRAM_API_TOKEN)} символов")
print(f"Используется токен Google длиной: {len(GOOGLE_API_KEY)} символов")

# Инициализация Google Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# ----------------------------- РАБОТА С БАЗОЙ ДАННЫХ -----------------------------

def init_db():
    """
    Создает и инициализирует базу данных SQLite.
    Создает необходимые таблицы, если они не существуют.
    """
    # Используем базу данных в папке /tmp для Railway
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Таблица пользователей - хранит основную информацию о пользователях
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        preferences TEXT,
        last_active TIMESTAMP
    )
    ''')
    
    # Таблица истории диалогов - хранит все сообщения для контекста
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        bot_response TEXT,
        timestamp TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Таблица челленджей - хранит все задания для пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        description TEXT,
        difficulty INTEGER,
        completed BOOLEAN,
        date_assigned TIMESTAMP,
        date_completed TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    conn.commit()
    return conn

# ----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ -----------------------------

def get_user(conn, user_id):
    """Получает информацию о пользователе из базы данных"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    return user

def add_user(conn, user_id, username, first_name):
    """Добавляет нового пользователя в базу данных"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, preferences, last_active) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, first_name, json.dumps({}), datetime.datetime.now())
    )
    conn.commit()

def update_user_preferences(conn, user_id, preferences):
    """Обновляет предпочтения пользователя"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET preferences = ? WHERE user_id = ?",
        (json.dumps(preferences), user_id)
    )
    conn.commit()

# ----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ИСТОРИЕЙ ЧАТА -----------------------------

def add_chat_history(conn, user_id, message, bot_response):
    """Сохраняет сообщение и ответ бота в историю чата"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (user_id, message, bot_response, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, message, bot_response, datetime.datetime.now())
    )
    conn.commit()

def get_recent_chat_history(conn, user_id, limit=5):
    """Получает последние сообщения из истории чата для контекста"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT message, bot_response FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    return cursor.fetchall()

# ----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ЧЕЛЛЕНДЖАМИ -----------------------------

def add_challenge(conn, user_id, category, description, difficulty):
    """Добавляет новый челлендж для пользователя"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO challenges (user_id, category, description, difficulty, completed, date_assigned) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, category, description, difficulty, False, datetime.datetime.now())
    )
    conn.commit()
    return cursor.lastrowid  # Возвращаем ID добавленного челленджа

def get_active_challenges(conn, user_id):
    """Получает все активные (незавершенные) челленджи пользователя"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, category, description, difficulty FROM challenges WHERE user_id = ? AND completed = 0",
        (user_id,)
    )
    return cursor.fetchall()

def complete_challenge(conn, challenge_id):
    """Отмечает челлендж как выполненный"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE challenges SET completed = 1, date_completed = ? WHERE id = ?",
        (datetime.datetime.now(), challenge_id)
    )
    conn.commit()

# ----------------------------- КАТЕГОРИИ ЧЕЛЛЕНДЖЕЙ -----------------------------

# Словарь с категориями челленджей и примерами для каждой категории
CHALLENGE_CATEGORIES = {
    "workout": ["Отжимания", "Приседания", "Планка", "Подтягивания", "Кардио", "Растяжка"],
    "programming": ["Python", "JavaScript", "Алгоритмы", "Структуры данных", "Web", "API"],
    "learning": ["Книги", "Языки", "Наука", "История", "Математика", "Технологии"],
    "lifestyle": ["Медитация", "Здоровое питание", "Сон", "Творчество", "Общение", "Организация"]
}

# ----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С AI -----------------------------

async def get_ai_response(prompt, context=None):
    """
    Получает ответ от Google Gemini AI на заданный вопрос
    
    Args:
        prompt (str): Вопрос или запрос пользователя
        context (list, optional): Список предыдущих сообщений для контекста
        
    Returns:
        str: Ответ от AI
    """
    try:
        # Создаем полный запрос с контекстом предыдущих сообщений
        full_prompt = ""
        if context:
            # Добавляем до 5 последних сообщений для контекста
            for msg, resp in context:
                full_prompt += f"Пользователь: {msg}\nАссистент: {resp}\n\n"
        
        full_prompt += f"Пользователь: {prompt}\nАссистент:"
        
        # Создаем модель Gemini и генерируем ответ
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(full_prompt)
        
        return response.text
    except Exception as e:
        logger.error(f"Ошибка при обращении к AI: {str(e)}")
        return f"Извините, произошла ошибка при обращении к AI: {str(e)}"

async def check_code(code, task):
    """
    Проверяет код с помощью AI и выдает рекомендации по исправлению ошибок
    
    Args:
        code (str): Код для проверки
        task (str): Описание задачи, для которой написан код
        
    Returns:
        str: Анализ кода с указанием ошибок и рекомендациями
    """
    try:
        prompt = f"""
        Проверь этот код для задачи: {task}
        
        ```
        {code}
        ```
        
        Найди ошибки, если они есть. Если код содержит ошибки, предоставь исправленную версию и объясни, что было неправильно.
        Если код правильный, подтверди это и объясни, почему он работает корректно.
        Формат ответа:
        1. Анализ кода
        2. Ошибки (если есть)
        3. Исправленный код (если нужно)
        4. Объяснение
        """
        
        # Создаем модель Gemini и генерируем ответ
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        logger.error(f"Ошибка при проверке кода: {str(e)}")
        return f"Извините, произошла ошибка при проверке кода: {str(e)}"

# ----------------------------- ГЕНЕРАТОР ЧЕЛЛЕНДЖЕЙ -----------------------------

async def generate_challenge(category, user_history=None, difficulty=1):
    """
    Генерирует новый челлендж с учетом категории, истории и сложности
    
    Args:
        category (str): Категория челленджа (workout, programming, learning, lifestyle)
        user_history (list, optional): История предыдущих челленджей пользователя
        difficulty (int): Уровень сложности от 1 до 5
        
    Returns:
        str: Текст нового челленджа
    """
    # Ограничиваем сложность от 1 до 5
    difficulty_level = min(max(difficulty, 1), 5)
    
    # Добавляем контекст из предыдущих челленджей
    history_context = ""
    if user_history:
        history_context = "Учитывая предыдущие челленджи пользователя: " + ", ".join([h[2] for h in user_history])
    
    # Формируем запрос для AI
    prompt = f"""
    Создай интересный и мотивирующий челлендж в категории "{category}" сложности {difficulty_level} из 5.
    {history_context}
    Челлендж должен быть конкретным, измеримым и выполнимым за один день.
    Не используй общие фразы. Предложи что-то специфичное и интересное.
    Ответ должен быть не длиннее 3-4 предложений.
    """
    
    # Создаем модель Gemini и генерируем ответ
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    
    return response.text

# ----------------------------- ОБРАБОТЧИКИ КОМАНД -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - начало работы с ботом"""
    conn = init_db()
    user = update.effective_user
    add_user(conn, user.id, user.username, user.first_name)
    
    # Создаем клавиатуру с основными кнопками
    keyboard = [
        [InlineKeyboardButton("📋 Мои челленджи", callback_data="my_challenges")],
        [InlineKeyboardButton("💪 Тренировки", callback_data="workout"), 
         InlineKeyboardButton("💻 Программирование", callback_data="programming")],
        [InlineKeyboardButton("📚 Обучение", callback_data="learning"), 
         InlineKeyboardButton("🌱 Образ жизни", callback_data="lifestyle")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я твой персональный AI-ассистент.\n\n"
        "Я могу отвечать на вопросы, давать ежедневные челленджи и помогать с программированием.\n\n"
        "Чем я могу помочь сегодня?",
        reply_markup=reply_markup
    )
    conn.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help - показывает список доступных команд"""
    help_text = """
*Доступные команды:*
/start - Начать взаимодействие с ботом
/help - Показать это сообщение
/challenge - Получить новый челлендж
/challenges - Просмотреть активные челленджи
/workout - Получить программу тренировок
/code - Проверить код (отправьте код после команды)

*Как пользоваться:*
- Задавайте любые вопросы напрямую
- Выбирайте категории челленджей через меню
- Отмечайте выполненные челленджи для прогресса
- Отправляйте свой код после команды /code для проверки

Удачи в выполнении челленджей! 🚀
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /challenge - предлагает выбрать категорию челленджа"""
    conn = init_db()
    user_id = update.effective_user.id
    
    # Клавиатура с категориями челленджей
    keyboard = [
        [InlineKeyboardButton("💪 Тренировки", callback_data="new_challenge_workout")],
        [InlineKeyboardButton("💻 Программирование", callback_data="new_challenge_programming")],
        [InlineKeyboardButton("📚 Обучение", callback_data="new_challenge_learning")],
        [InlineKeyboardButton("🌱 Образ жизни", callback_data="new_challenge_lifestyle")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Выберите категорию для нового челленджа:",
        reply_markup=reply_markup
    )
    conn.close()

async def challenges_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /challenges - показывает список активных челленджей"""
    conn = init_db()
    user_id = update.effective_user.id
    
    # Получаем активные челленджи пользователя
    active_challenges = get_active_challenges(conn, user_id)
    
    if not active_challenges:
        await update.message.reply_text(
            "У вас пока нет активных челленджей. Используйте /challenge, чтобы получить новый!"
        )
    else:
        response = "Ваши активные челленджи:\n\n"
        
        # Формируем список челленджей
        for idx, (challenge_id, category, description, difficulty) in enumerate(active_challenges, 1):
            stars = "⭐" * difficulty
            response += f"{idx}. [{category}] {stars}\n{description}\n\n"
            
        # Создаем кнопки для отметки выполненных челленджей
        keyboard = [[InlineKeyboardButton(f"Выполнил челлендж #{i+1}", callback_data=f"complete_{cid}")]
                   for i, (cid, _, _, _) in enumerate(active_challenges)]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup)
    
    conn.close()

async def workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /workout - генерирует программу тренировки на сегодня"""
    conn = init_db()
    user_id = update.effective_user.id
    
    # Получаем историю пользователя для контекста
    history = get_recent_chat_history(conn, user_id, 5)
    
    # Определяем день недели для персонализации тренировки
    today = datetime.datetime.now().strftime("%A").lower()
    
    # Формируем запрос для AI
    prompt = f"""
    Создай программу тренировки на сегодня ({today}). 
    Добавь основную тренировку и один бонусный челлендж.
    Программа должна быть конкретной, с указанием упражнений, подходов и повторений.
    Челлендж должен быть интересным дополнением к тренировке.
    """
    
    # Получаем ответ от AI
    workout_plan = await get_ai_response(prompt, history)
    
    # Отправляем пользователю и сохраняем в историю
    await update.message.reply_text(workout_plan)
    add_chat_history(conn, user_id, prompt, workout_plan)
    
    conn.close()

async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /code - проверяет код пользователя
    Пример использования: /code print("Hello, world!")
    """
    # Проверяем, есть ли код после команды
    if not context.args:
        # Если кода нет, просим пользователя отправить его
        context.user_data['waiting_for_code'] = True
        context.user_data['code_task'] = "общая проверка кода"
        
        await update.message.reply_text(
            "Пожалуйста, отправьте код после команды /code или ответьте на это сообщение с вашим кодом."
        )
        return
    
    # Если код есть, объединяем все аргументы в строку
    code = " ".join(context.args)
    task = "общая проверка кода"
    
    # Проверяем код с помощью AI
    result = await check_code(code, task)
    
    # Отправляем результат пользователю
    await update.message.reply_text(result, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных текстовых сообщений от пользователя"""
    conn = init_db()
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Проверяем, ожидаем ли мы код от пользователя
    if context.user_data.get('waiting_for_code'):
        task = context.user_data.get('code_task', 'Проверка кода')
        result = await check_code(message_text, task)
        await update.message.reply_text(result, parse_mode='Markdown')
        context.user_data['waiting_for_code'] = False
        return
    
    # Получаем историю для контекста
    history = get_recent_chat_history(conn, user_id, 5)
    
    # Получаем ответ от AI
    response = await get_ai_response(message_text, history)
    
    # Отправляем ответ пользователю
    await update.message.reply_text(response)
    
    # Сохраняем историю диалога
    add_chat_history(conn, user_id, message_text, response)
    
    conn.close()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки интерактивного меню"""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки
    
    conn = init_db()
    user_id = query.from_user.id
    callback_data = query.data
    
    # Обработка запроса на создание нового челленджа
    if callback_data.startswith("new_challenge_"):
        category = callback_data.replace("new_challenge_", "")
        
        # Получаем историю челленджей пользователя
        active_challenges = get_active_challenges(conn, user_id)
        
        # Определяем сложность на основе истории
        user_challenges = get_active_challenges(conn, user_id)
        difficulty = min(len(user_challenges) // 3 + 1, 5)  # Увеличиваем сложность каждые 3 выполненных челленджа
        
        # Генерируем новый челлендж
        challenge = await generate_challenge(category, active_challenges, difficulty)
        
        # Сохраняем челлендж в базу данных
        challenge_id = add_challenge(conn, user_id, category, challenge, difficulty)
        
        # Создаем кнопки для челленджа
        keyboard = [
            [InlineKeyboardButton("✅ Выполнено", callback_data=f"complete_{challenge_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем челлендж пользователю
        await query.edit_message_text(
            f"Ваш новый челлендж в категории '{category}':\n\n{challenge}\n\n"
            f"Сложность: {'⭐' * difficulty}\n\nУдачи! 💪",
            reply_markup=reply_markup
        )
    
    # Обработка отметки о выполнении челленджа
    elif callback_data.startswith("complete_"):
        challenge_id = int(callback_data.replace("complete_", ""))
        complete_challenge(conn, challenge_id)
        
        # Отправляем поздравление
        await query.edit_message_text(
            "Поздравляем с выполнением челленджа! 🎉\n\n"
            "Используйте /challenge, чтобы получить новый челлендж, или /challenges, чтобы увидеть оставшиеся.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🆕 Новый челлендж", callback_data="new_challenge")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
            ])
        )
    
    # Показ списка активных челленджей
    elif callback_data == "my_challenges":
        active_challenges = get_active_challenges(conn, user_id)
        
        if not active_challenges:
            await query.edit_message_text(
                "У вас пока нет активных челленджей. Используйте команду ниже, чтобы получить новый!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🆕 Новый челлендж", callback_data="new_challenge")]])
            )
        else:
            response = "Ваши активные челленджи:\n\n"
            
            for idx, (challenge_id, category, description, difficulty) in enumerate(active_challenges, 1):
                stars = "⭐" * difficulty
                response += f"{idx}. [{category}] {stars}\n{description}\n\n"
                
            keyboard = [[InlineKeyboardButton(f"Выполнил челлендж #{i+1}", callback_data=f"complete_{cid}")]
                       for i, (cid, _, _, _) in enumerate(active_challenges)]
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, reply_markup=reply_markup)
    
    # Меню выбора категории для нового челленджа
    elif callback_data == "new_challenge":
        keyboard = [
            [InlineKeyboardButton("💪 Тренировки", callback_data="new_challenge_workout")],
            [InlineKeyboardButton("💻 Программирование", callback_data="new_challenge_programming")],
            [InlineKeyboardButton("📚 Обучение", callback_data="new_challenge_learning")],
            [InlineKeyboardButton("🌱 Образ жизни", callback_data="new_challenge_lifestyle")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Выберите категорию для нового челленджа:",
            reply_markup=reply_markup
        )
    
    # Возврат в главное меню
    elif callback_data == "back_to_menu":
        keyboard = [
            [InlineKeyboardButton("📋 Мои челленджи", callback_data="my_challenges")],
            [InlineKeyboardButton("💪 Тренировки", callback_data="workout"), 
             InlineKeyboardButton("💻 Программирование", callback_data="programming")],
            [InlineKeyboardButton("📚 Обучение", callback_data="learning"), 
             InlineKeyboardButton("🌱 Образ жизни", callback_data="lifestyle")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Чем я могу помочь сегодня?",
            reply_markup=reply_markup
        )
    
    # Быстрый выбор категории для челленджа
    elif callback_data in ["workout", "programming", "learning", "lifestyle"]:
        category = callback_data
        
        # Определяем сложность на основе истории
        user_challenges = get_active_challenges(conn, user_id)
        difficulty = min(len(user_challenges) // 3 + 1, 5)
        
        # Генерируем новый челлендж
        challenge = await generate_challenge(category, user_challenges, difficulty)
        
        # Сохраняем челлендж в базу данных
        challenge_id = add_challenge(conn, user_id, category, challenge, difficulty)
        
        # Создаем кнопки
        keyboard = [
            [InlineKeyboardButton("✅ Выполнено", callback_data=f"complete_{challenge_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем челлендж
        await query.edit_message_text(
            f"Ваш новый челлендж в категории '{category}':\n\n{challenge}\n\n"
            f"Сложность: {'⭐' * difficulty}\n\nУдачи! 💪",
            reply_markup=reply_markup
        )
    
    # Меню настроек
    elif callback_data == "settings":
        # Простое меню настроек
        keyboard = [
            [InlineKeyboardButton("🔄 Сбросить прогресс", callback_data="reset_progress")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Настройки:\n\nЗдесь вы можете управлять своими предпочтениями.",
            reply_markup=reply_markup
        )
    
    conn.close()

# ----------------------------- ОСНОВНАЯ ФУНКЦИЯ -----------------------------

def main():
    """Основная функция для запуска бота"""
    # Инициализация базы данных
    conn = init_db()
    conn.close()
    
    # Создание и настройка приложения
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("challenge", challenge_command))
    application.add_handler(CommandHandler("challenges", challenges_command))
    application.add_handler(CommandHandler("workout", workout_command))
    application.add_handler(CommandHandler("code", code_command))
    
    # Обработчик кнопок меню
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота в режиме webhook для Railway
    PORT = int(os.environ.get('PORT', 8443))
    
    # Для продакшена используем webhook, если указан URL
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
    if WEBHOOK_URL:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_API_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_API_TOKEN}"
        )
    else:
        # Для локальной разработки или если webhook не настроен используем polling
        print("Бот запущен в режиме polling. Нажмите Ctrl+C для остановки.")
        application.run_polling()

# ----------------------------- ЗАПУСК БОТА -----------------------------

if __name__ == "__main__":
    main()
