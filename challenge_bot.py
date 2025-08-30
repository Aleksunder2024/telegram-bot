import os
import json
import random
import datetime
import sqlite3
import logging
from typing import Dict, List, Optional, Union

# Для работы с Telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Для HTTP запросов
import requests

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токены API (жестко закодированные для Railway)
TELEGRAM_API_TOKEN = "8416538451:AAEjOIDh_XskQ39xvvHkN7IGIqLmVijBAKI"
HUGGINGFACE_API_TOKEN = "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"  # Бесплатный токен для HuggingFace

# Используем переменные окружения, если они заданы
if os.getenv("TELEGRAM_API_TOKEN"):
    TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if os.getenv("HUGGINGFACE_API_TOKEN"):
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

print(f"Используется токен Telegram длиной: {len(TELEGRAM_API_TOKEN)} символов")

# ----------------------------- РАБОТА С БАЗОЙ ДАННЫХ -----------------------------

def init_db():
    """Создает и инициализирует базу данных SQLite."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            preferences TEXT,
            last_active TIMESTAMP
        )
        ''')
        
        # Таблица истории диалогов
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
        
        # Таблица челленджей
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
        print("База данных успешно инициализирована")
    except sqlite3.Error as e:
        print(f"Ошибка при инициализации базы данных: {e}")
    
    return conn

# ----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ -----------------------------

def get_user(conn, user_id):
    """Получает информацию о пользователе из базы данных"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        return user
    except sqlite3.Error as e:
        print(f"Ошибка при получении пользователя: {e}")
        return None

def add_user(conn, user_id, username, first_name):
    """Добавляет нового пользователя в базу данных"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, preferences, last_active) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, json.dumps({}), datetime.datetime.now())
        )
        conn.commit()
        print(f"Пользователь добавлен: {user_id}, {username}")
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении пользователя: {e}")

def add_chat_history(conn, user_id, message, bot_response):
    """Сохраняет сообщение и ответ бота в историю чата"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (user_id, message, bot_response, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, message, bot_response, datetime.datetime.now())
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении истории чата: {e}")

def get_recent_chat_history(conn, user_id, limit=5):
    """Получает последние сообщения из истории чата для контекста"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message, bot_response FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Ошибка при получении истории чата: {e}")
        return []

# ----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ЧЕЛЛЕНДЖАМИ -----------------------------

def add_challenge(conn, user_id, category, description, difficulty):
    """Добавляет новый челлендж для пользователя"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO challenges (user_id, category, description, difficulty, completed, date_assigned) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, category, description, difficulty, False, datetime.datetime.now())
        )
        conn.commit()
        return cursor.lastrowid  # Возвращаем ID добавленного челленджа
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении челленджа: {e}")
        return None

def get_active_challenges(conn, user_id):
    """Получает все активные (незавершенные) челленджи пользователя"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, category, description, difficulty FROM challenges WHERE user_id = ? AND completed = 0",
            (user_id,)
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Ошибка при получении активных челленджей: {e}")
        return []

def complete_challenge(conn, challenge_id):
    """Отмечает челлендж как выполненный"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE challenges SET completed = 1, date_completed = ? WHERE id = ?",
            (datetime.datetime.now(), challenge_id)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при завершении челленджа: {e}")

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
    """Получает ответ от AI на заданный вопрос через HuggingFace API."""
    try:
        # Используем HuggingFace API
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        
        # Формируем полный запрос с контекстом предыдущих сообщений
        full_prompt = ""
        if context:
            # Добавляем до 5 последних сообщений для контекста
            for msg, resp in context:
                full_prompt += f"Пользователь: {msg}\nАссистент: {resp}\n\n"
        
        full_prompt += f"Пользователь: {prompt}\nАссистент:"
        
        # Отправляем запрос
        payload = {"inputs": full_prompt, "max_length": 500}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # Проверяем наличие ошибок
        if response.status_code != 200:
            logger.error(f"Ошибка API: {response.status_code}, {response.text}")
            return f"Извините, не удалось получить ответ (код ошибки: {response.status_code}). Попробуйте еще раз позже."
        
        # Обрабатываем ответ
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            ai_response = result[0]["generated_text"].split("Ассистент:")[-1].strip()
            return ai_response
        else:
            # Если результат не в ожидаемом формате, возвращаем резервный ответ
            return "Извините, я не смог обработать этот запрос."
        
    except Exception as e:
        logger.error(f"Ошибка при обращении к AI: {str(e)}")
        return f"Извините, произошла ошибка: {str(e)}"

async def check_code(code, task):
    """Проверяет код с помощью AI и выдает рекомендации по исправлению ошибок"""
    try:
        # Используем HuggingFace API
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        
        prompt = f"""
        Проверь этот код для задачи: {task}
        
        ```
        {code}
        ```
        
        Найди ошибки, если они есть. Если код содержит ошибки, предоставь исправленную версию и объясни, что было неправильно.
        Если код правильный, подтверди это и объясни, почему он работает корректно.
        """
        
        # Отправляем запрос
        payload = {"inputs": prompt, "max_length": 800}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        # Проверяем наличие ошибок
        if response.status_code != 200:
            logger.error(f"Ошибка API при проверке кода: {response.status_code}, {response.text}")
            return f"Извините, не удалось проверить код. Попробуйте еще раз позже."
        
        # Обрабатываем ответ
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0]["generated_text"]
        else:
            return "Извините, я не смог проанализировать ваш код."
        
    except Exception as e:
        logger.error(f"Ошибка при проверке кода: {str(e)}")
        return f"Извините, произошла ошибка при проверке кода: {str(e)}"

async def generate_challenge(category, user_history=None, difficulty=1):
    """Генерирует новый челлендж с учетом категории, истории и сложности"""
    try:
        # Ограничиваем сложность от 1 до 5
        difficulty_level = min(max(difficulty, 1), 5)
        
        # Если API недоступен, используем предустановленные челленджи
        predefined_challenges = {
            "workout": [
                "Выполните 3 подхода по 15 отжиманий с разным положением рук",
                "Пробегите 3 км на свежем воздухе или 20 минут на беговой дорожке",
                "Выполните 100 приседаний, разбив их на удобные подходы",
                "Сделайте планку 3 раза по 1 минуте с 30-секундным отдыхом",
                "Выполните тренировку HIIT: 30 секунд максимальной интенсивности, 30 секунд отдыха, 10 раундов"
            ],
            "programming": [
                "Напишите функцию для обращения строки без использования встроенных методов",
                "Создайте простой калькулятор с использованием функций",
                "Напишите программу для проверки, является ли строка палиндромом",
                "Создайте программу, которая находит сумму всех чисел от 1 до N",
                "Разработайте простую игру 'Угадай число' с подсказками"
            ],
            "learning": [
                "Выучите 10 новых слов на иностранном языке и составьте с ними предложения",
                "Прочитайте статью на новую тему и запишите 5 ключевых идей",
                "Посмотрите образовательное видео и напишите краткий конспект",
                "Изучите основы новой темы через онлайн-курс или учебник",
                "Нарисуйте ментальную карту по теме, которую вы изучаете"
            ],
            "lifestyle": [
                "Практикуйте медитацию в течение 10 минут утром и вечером",
                "Приготовьте новое здоровое блюдо по рецепту",
                "Проведите день без социальных сетей и заметьте, как изменилось ваше самочувствие",
                "Составьте план на неделю с распределением времени на важные задачи",
                "Напишите список из 10 вещей, за которые вы благодарны"
            ]
        }
        
        # Выбираем челлендж из предустановленных в зависимости от сложности
        challenge_index = min(difficulty_level - 1, len(predefined_challenges[category]) - 1)
        selected_challenge = predefined_challenges[category][challenge_index]
        
        # Пытаемся получить челлендж через API
        try:
            API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
            headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
            
            prompt = f"Создай мотивирующий челлендж в категории '{category}' сложности {difficulty_level} из 5."
            
            payload = {"inputs": prompt, "max_length": 300}
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    api_challenge = result[0]["generated_text"]
                    if len(api_challenge) > 20:  # Проверяем, что ответ не слишком короткий
                        return api_challenge
        except:
            pass  # В случае ошибки используем предустановленный челлендж
            
        return f"{selected_challenge}. Сложность: {difficulty_level}/5."
        
    except Exception as e:
        logger.error(f"Ошибка при генерации челленджа: {str(e)}")
        # Резервный вариант: создаем челлендж без использования AI
        examples = CHALLENGE_CATEGORIES.get(category, ["новое задание"])
        return f"Ваш челлендж на сегодня: {random.choice(examples)}. Выполните его с максимальной отдачей! Сложность: {difficulty}/5."

# ----------------------------- ОБРАБОТЧИКИ КОМАНД -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - начало работы с ботом"""
    try:
        conn = init_db()
        user = update.effective_user
        add_user(conn, user.id, user.username, user.first_name)
        
        # Создаем клавиатуру с основными кнопками
        keyboard = [
            [InlineKeyboardButton("📋 Мои челленджи", callback_data="my_challenges")],
            [InlineKeyboardButton("💪 Тренировки", callback_data="workout"), 
             InlineKeyboardButton("💻 Программирование", callback_data="programming")],
            [InlineKeyboardButton("📚 Обучение", callback_data="learning"), 
             InlineKeyboardButton("🌱 Образ жизни", callback_data="lifestyle")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Привет, {user.first_name}! Я твой персональный AI-ассистент.\n\n"
            "Я могу отвечать на вопросы, давать ежедневные челленджи и помогать с программированием.\n\n"
            "Чем я могу помочь сегодня?",
            reply_markup=reply_markup
        )
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}")
        await update.message.reply_text(
            f"Привет! Произошла ошибка при запуске. Пожалуйста, попробуйте снова или используйте команду /help."
        )

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
    try:
        conn = init_db()
        
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
    except Exception as e:
        logger.error(f"Ошибка в обработчике challenge_command: {e}")
        await update.message.reply_text(
            "Произошла ошибка при выборе челленджа. Пожалуйста, попробуйте снова."
        )

async def challenges_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /challenges - показывает список активных челленджей"""
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в обработчике challenges_command: {e}")
        await update.message.reply_text(
            "Произошла ошибка при получении списка челленджей. Пожалуйста, попробуйте снова."
        )

async def workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /workout - генерирует программу тренировки на сегодня"""
    try:
        conn = init_db()
        user_id = update.effective_user.id
        
        # Заготовленные программы тренировок
        workout_plans = [
            "**Тренировка на сегодня**\n\n"
            "**Разминка:**\n- 5 минут легкий бег или прыжки на скакалке\n- 10 круговых движений руками\n- 10 круговых движений тазом\n\n"
            "**Основная часть:**\n- 3x15 приседаний\n- 3x10 отжиманий\n- 3x30 сек планка\n- 3x10 выпадов на каждую ногу\n- 3x15 скручиваний\n\n"
            "**Бонусный челлендж:** Попробуйте выполнить 5 бурпи без остановки",
            
            "**Кардио тренировка**\n\n"
            "**Разминка:**\n- 5 минут ходьбы с постепенным ускорением\n\n"
            "**Основная часть:**\n- 1 минута бега + 30 секунд ходьбы (повторить 8 раз)\n- 30 прыжков с разведением рук и ног\n- 30 секунд бег на месте с высоким подниманием колен\n\n"
            "**Бонусный челлендж:** Пройдите 10 000 шагов в течение дня",
            
            "**Силовая тренировка**\n\n"
            "**Разминка:**\n- 10 приседаний\n- 10 отжиманий с колен\n- 10 наклонов в стороны\n\n"
            "**Основная часть:**\n- 3x12 приседаний с прыжком\n- 3x8 отжиманий\n- 3x15 подъемов корпуса из положения лежа\n- 3x12 обратных отжиманий от стула\n\n"
            "**Бонусный челлендж:** Выполните максимальное количество отжиманий без остановки"
        ]
        
        # Выбираем случайную программу
        workout_plan = random.choice(workout_plans)
        
        # Пытаемся получить персонализированную программу через API
        try:
            response = await get_ai_response("Создай программу тренировки на сегодня с основной частью и бонусным челленджем.")
            if len(response) > 50:  # Проверяем, что ответ достаточно длинный
                workout_plan = response
        except:
            pass  # В случае ошибки используем предустановленную программу
        
        # Отправляем пользователю и сохраняем в историю
        await update.message.reply_text(workout_plan)
        add_chat_history(conn, user_id, "Создай программу тренировки", workout_plan)
        
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в обработчике workout_command: {e}")
        await update.message.reply_text(
            "Произошла ошибка при создании программы тренировки. Пожалуйста, попробуйте снова позже."
        )

async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /code - проверяет код пользователя"""
    try:
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
        
        # Отправляем сообщение о проверке
        await update.message.reply_text("Проверяю ваш код...")
        
        # Проверяем код с помощью AI
        result = await check_code(code, task)
        
        # Отправляем результат пользователю
        await update.message.reply_text(result, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка в обработчике code_command: {e}")
        await update.message.reply_text(
            "Произошла ошибка при проверке кода. Пожалуйста, убедитесь, что код правильно отформатирован и попробуйте снова."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных текстовых сообщений от пользователя"""
    try:
        conn = init_db()
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Проверяем, ожидаем ли мы код от пользователя
        if context.user_data.get('waiting_for_code'):
            task = context.user_data.get('code_task', 'Проверка кода')
            
            # Отправляем сообщение о проверке
            await update.message.reply_text("Проверяю ваш код...")
            
            result = await check_code(message_text, task)
            await update.message.reply_text(result, parse_mode='Markdown')
            context.user_data['waiting_for_code'] = False
            return
        
        # Получаем историю для контекста
        history = get_recent_chat_history(conn, user_id, 5)
        
        # Отправляем сообщение "печатает..."
        await update.message.chat.send_action(action="typing")
        
        # Получаем ответ от AI
        response = await get_ai_response(message_text, history)
        
        # Отправляем ответ пользователю
        await update.message.reply_text(response)
        
        # Сохраняем историю диалога
        add_chat_history(conn, user_id, message_text, response)
        
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в обработчике handle_message: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего сообщения. Пожалуйста, попробуйте снова."
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки интерактивного меню"""
    try:
        query = update.callback_query
        await query.answer()  # Подтверждаем нажатие кнопки
        
        conn = init_db()
        user_id = query.from_user.id
        callback_data = query.data
        
        # Обработка запроса на создание нового челленджа
        if callback_data.startswith("new_challenge_"):
            category = callback_data.replace("new_challenge_", "")
            
            # Сообщаем пользователю, что генерируем челлендж
            await query.edit_message_text("Создаю новый челлендж для вас...")
            
            # Определяем сложность на основе истории
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM challenges WHERE user_id = ? AND completed = 1", (user_id,))
                completed_count = cursor.fetchone()[0]
                difficulty = min(completed_count // 3 + 1, 5)  # Увеличиваем сложность каждые 3 выполненных челленджа
            except:
                difficulty = 1
            
            # Генерируем новый челлендж
            challenge = await generate_challenge(category, None, difficulty)
            
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
                 InlineKeyboardButton("🌱 Образ жизни", callback_data="lifestyle")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"Чем я могу помочь сегодня?",
                reply_markup=reply_markup
            )
        
        # Быстрый выбор категории для челленджа
        elif callback_data in ["workout", "programming", "learning", "lifestyle"]:
            category = callback_data
            
            # Сообщаем пользователю, что генерируем челлендж
            await query.edit_message_text("Создаю новый челлендж для вас...")
            
            # Определяем сложность
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM challenges WHERE user_id = ? AND completed = 1", (user_id,))
                completed_count = cursor.fetchone()[0]
                difficulty = min(completed_count // 3 + 1, 5)
            except:
                difficulty = 1
            
            # Генерируем новый челлендж
            challenge = await generate_challenge(category, None, difficulty)
            
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
        
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в обработчике button_handler: {e}")
        try:
            await query.edit_message_text(
                "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте снова или используйте команду /start."
            )
        except:
            pass

# ----------------------------- ОСНОВНАЯ ФУНКЦИЯ -----------------------------

def main():
    """Основная функция для запуска бота"""
    try:
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
        
        # Запуск бота в режиме polling
        print("Бот запущен в режиме polling! Нажмите Ctrl+C для остановки.")
        application.run_polling()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        print(f"Критическая ошибка: {e}")

# ----------------------------- ЗАПУСК БОТА -----------------------------

if __name__ == "__main__":
    main()
