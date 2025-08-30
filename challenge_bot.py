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

# ----------------------------- СТРУКТУРА ОБУЧЕНИЯ PYTHON -----------------------------
# Структура данных для хранения курса Python
PYTHON_COURSE = {
    "level_1": {
        "title": "Основы Python",
        "modules": {
            "module_1": {
                "title": "Первые шаги",
                "lessons": {
                    "lesson_1": {
                        "title": "Введение в Python",
                        "theory": """
# Введение в Python

Python - это популярный язык программирования, созданный в 1991 году. Он известен своей читаемостью и простотой синтаксиса.

## Почему Python?

- **Простой синтаксис**: легко читать и писать
- **Универсальность**: подходит для веб-разработки, анализа данных, ИИ, автоматизации
- **Большое сообщество**: множество библиотек и ресурсов

## Области применения Python:

- Веб-разработка (Django, Flask)
- Анализ данных (Pandas, NumPy)
- Машинное обучение (TensorFlow, PyTorch)
- Автоматизация процессов
- Разработка игр
- И многое другое!

В этом курсе мы начнем с самых основ и постепенно перейдем к более сложным темам.
                        """,
                        "practice": {
                            "task": "Нажмите кнопку, соответствующую правильному ответу: Когда был создан Python?",
                            "type": "quiz",
                            "options": ["1989", "1991", "2000", "2005"],
                            "correct": 1
                        }
                    },
                    "lesson_2": {
                        "title": "Первая программа",
                        "theory": """
# Ваша первая программа на Python

Давайте напишем традиционную первую программу - "Hello, World!". В Python это очень просто:

```python
print("Hello, World!")
Функция print() выводит текст или значение на экран. Текст в Python заключается в кавычки (одинарные или двойные).

Запуск программы
Когда вы выполняете эту команду, Python обрабатывает ее и выводит текст:

text

Hello, World!
Эксперименты
Попробуйте вывести другие сообщения:

Python

print("Привет, мир!")
print("Я учу Python!")
Python выполняет команды последовательно, сверху вниз, поэтому оба сообщения будут выведены в том порядке, в котором они написаны.
""",
"practice": {
"task": "Напишите программу, которая выводит фразу: Я начинаю изучать Python!",
"type": "code",
"solution": "print("Я начинаю изучать Python!")",
"hint": "Используйте функцию print() и не забудьте про кавычки."
}
},
"lesson_3": {
"title": "Переменные и типы данных",
"theory": """

Переменные и типы данных
Переменные в программировании - это контейнеры для хранения данных.

Создание переменных в Python
В Python вы создаете переменную, присваивая ей значение:

Python

name = "Алексей"
age = 25
height = 1.75
is_student = True
Основные типы данных
Строки (str) - для текста:

Python

name = "Python"
message = 'Привет, мир!'
Числа:

Целые числа (int):
Python

age = 25
count = -10
Числа с плавающей точкой (float):
Python

price = 19.99
temperature = -2.5
Логические значения (bool):

Python

is_active = True
has_completed = False
Проверка типа данных
Функция type() позволяет узнать тип данных:

Python

x = 10
print(type(x))  # Выведет: <class 'int'>

y = "Hello"
print(type(y))  # Выведет: <class 'str'>
Преобразование типов
Вы можете преобразовывать данные из одного типа в другой:

Python

# Строка в число
age_str = "25"
age_num = int(age_str)  # Теперь это число 25

# Число в строку
price = 19.99
price_str = str(price)  # Теперь это строка "19.99"
text

                    """,
                    "practice": {
                        "task": "Создайте переменную name со значением вашего имени и переменную year со значением текущего года. Затем выведите обе переменные в одной строке через пробел.",
                        "type": "code",
                        "solution": "name = \"Ваше_имя\"\nyear = 2025\nprint(name, year)",
                        "hint": "Создайте две переменные и используйте функцию print() с несколькими аргументами."
                    }
                }
            }
        },
        "module_2": {
            "title": "Основные операции",
            "lessons": {
                "lesson_1": {
                    "title": "Арифметические операции",
                    "theory": """
Арифметические операции в Python
Python поддерживает все стандартные математические операции.

Основные операторы
Сложение +: 5 + 3 (результат: 8)
Вычитание -: 10 - 4 (результат: 6)
Умножение *: 4 * 3 (результат: 12)
Деление /: 8 / 4 (результат: 2.0)
Целочисленное деление //: 9 // 2 (результат: 4) - округляет вниз
Остаток от деления %: 10 % 3 (результат: 1)
Возведение в степень **: 2 ** 3 (результат: 8)
Порядок операций
Python следует стандартному математическому порядку операций:

Скобки ()
Возведение в степень **
Умножение *, деление /, целочисленное деление //, остаток %
Сложение +, вычитание -
Пример:

Python

result = 2 + 3 * 4  # Результат: 14, а не 20
print(result)

result_with_brackets = (2 + 3) * 4  # Результат: 20
print(result_with_brackets)
Операции с переменными
Python

a = 10
b = 3

sum_result = a + b  # 13
diff_result = a - b  # 7
mul_result = a * b  # 30
div_result = a / b  # 3.3333...

print(f"Сумма: {sum_result}")
print(f"Разность: {diff_result}")
print(f"Произведение: {mul_result}")
print(f"Частное: {div_result}")
Сокращенные операторы присваивания
a += 5 (эквивалентно a = a + 5)
a -= 3 (эквивалентно a = a - 3)
a *= 2 (эквивалентно a = a * 2)
a /= 4 (эквивалентно a = a / 4)
""",
"practice": {
"task": "Напишите программу, которая вычисляет среднее арифметическое трех чисел: 10, 15 и 20.",
"type": "code",
"solution": "num1 = 10\nnum2 = 15\nnum3 = 20\naverage = (num1 + num2 + num3) / 3\nprint(average)",
"hint": "Сложите три числа и разделите сумму на 3."
}
}
}
}
}
}
}
----------------------------- РАБОТА С БАЗОЙ ДАННЫХ -----------------------------
def init_db():
"""Создает и инициализирует базу данных SQLite."""
db_path = os.path.join(os.path.dirname(os.path.abspath(file)), 'bot_database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

text

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
    
    # Таблица прогресса по Python
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS python_progress (
        user_id INTEGER PRIMARY KEY,
        current_level TEXT,
        current_module TEXT,
        current_lesson TEXT,
        completed_lessons TEXT,
        points INTEGER DEFAULT 0,
        last_activity TIMESTAMP
    )
    ''')
    
    conn.commit()
    print("База данных успешно инициализирована")
except sqlite3.Error as e:
    print(f"Ошибка при инициализации базы данных: {e}")

return conn
----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ -----------------------------
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

----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ЧЕЛЛЕНДЖАМИ -----------------------------
def add_challenge(conn, user_id, category, description, difficulty):
"""Добавляет новый челлендж для пользователя"""
try:
cursor = conn.cursor()
cursor.execute(
"INSERT INTO challenges (user_id, category, description, difficulty, completed, date_assigned) VALUES (?, ?, ?, ?, ?, ?)",
(user_id, category, description, difficulty, False, datetime.datetime.now())
)
conn.commit()
return cursor.lastrowid # Возвращаем ID добавленного челленджа
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

----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ОБУЧЕНИЕМ PYTHON -----------------------------
def get_user_python_progress(conn, user_id):
"""Получает прогресс пользователя по курсу Python"""
try:
cursor = conn.cursor()
cursor.execute("SELECT * FROM python_progress WHERE user_id = ?", (user_id,))
progress = cursor.fetchone()

text

    if not progress:
        # Инициализация прогресса для нового пользователя
        cursor.execute(
            "INSERT INTO python_progress (user_id, current_level, current_module, current_lesson, completed_lessons, points, last_activity) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, "level_1", "module_1", "lesson_1", json.dumps([]), 0, datetime.datetime.now())
        )
        conn.commit()
        cursor.execute("SELECT * FROM python_progress WHERE user_id = ?", (user_id,))
        progress = cursor.fetchone()
    
    return progress
except sqlite3.Error as e:
    print(f"Ошибка при получении прогресса Python: {e}")
    # Возвращаем базовые значения в случае ошибки
    return (user_id, "level_1", "module_1", "lesson_1", json.dumps([]), 0, datetime.datetime.now())
def update_user_python_progress(conn, user_id, level=None, module=None, lesson=None, add_completed=None, add_points=0):
"""Обновляет прогресс пользователя по курсу Python"""
try:
cursor = conn.cursor()

text

    # Получаем текущий прогресс
    current = get_user_python_progress(conn, user_id)
    
    # Преобразуем список выполненных уроков из JSON
    completed_lessons = json.loads(current[4])
    
    # Добавляем новый выполненный урок, если указан
    if add_completed:
        lesson_key = f"{current[1]}_{current[2]}_{current[3]}"
        if lesson_key not in completed_lessons:
            completed_lessons.append(lesson_key)
    
    # Обновляем значения
    new_level = level if level else current[1]
    new_module = module if module else current[2]
    new_lesson = lesson if lesson else current[3]
    new_points = current[5] + add_points
    
    # Обновляем запись в базе данных
    cursor.execute(
        "UPDATE python_progress SET current_level = ?, current_module = ?, current_lesson = ?, completed_lessons = ?, points = ?, last_activity = ? WHERE user_id = ?",
        (new_level, new_module, new_lesson, json.dumps(completed_lessons), new_points, datetime.datetime.now(), user_id)
    )
    conn.commit()
except sqlite3.Error as e:
    print(f"Ошибка при обновлении прогресса Python: {e}")
----------------------------- КАТЕГОРИИ ЧЕЛЛЕНДЖЕЙ -----------------------------
Словарь с категориями челленджей и примерами для каждой категории
CHALLENGE_CATEGORIES = {
"workout": ["Отжимания", "Приседания", "Планка", "Подтягивания", "Кардио", "Растяжка"],
"programming": ["Python", "JavaScript", "Алгоритмы", "Структуры данных", "Web", "API"],
"learning": ["Книги", "Языки", "Наука", "История", "Математика", "Технологии"],
"lifestyle": ["Медитация", "Здоровое питание", "Сон", "Творчество", "Общение", "Организация"]
}

----------------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С AI -----------------------------
async def get_ai_response(prompt, context=None):
"""Получает ответ от AI на заданный вопрос через HuggingFace API."""
try:
# Используем HuggingFace API
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

text

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

text

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

text

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
----------------------------- ОБРАБОТЧИКИ КОМАНД -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
"""Обработчик команды /start - начало работы с ботом"""
try:
conn = init_db()
user = update.effective_user
add_user(conn, user.id, user.username, user.first_name)

text

    # Создаем клавиатуру с основными кнопками
    keyboard = [
        [InlineKeyboardButton("📋 Мои челленджи", callback_data="my_challenges")],
        [InlineKeyboardButton("💪 Тренировки", callback_data="workout"), 
         InlineKeyboardButton("💻 Программирование", callback_data="programming")],
        [InlineKeyboardButton("📚 Обучение", callback_data="learning"), 
         InlineKeyboardButton("🌱 Образ жизни", callback_data="lifestyle")],
        [InlineKeyboardButton("🐍 Изучить Python", callback_data="python_back")]
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
Доступные команды:
/start - Начать взаимодействие с ботом
/help - Показать это сообщение
/challenge - Получить новый челлендж
/challenges - Просмотреть активные челленджи
/workout - Получить программу тренировок
/code - Проверить код (отправьте код после команды)
/learn - Начать изучение Python с нуля

Как пользоваться:

Задавайте любые вопросы напрямую
Выбирайте категории челленджей через меню
Отмечайте выполненные челленджи для прогресса
Отправляйте свой код после команды /code для проверки
Используйте курс Python для изучения программирования
Удачи в выполнении челленджей и обучении! 🚀
"""

text

await update.message.reply_text(help_text, parse_mode='Markdown')
async def challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
"""Обработчик команды /challenge - предлагает выбрать категорию челленджа"""
try:
conn = init_db()

text

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

text

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

text

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
context.user_data['waiting_for_python_code'] = False
context.user_data['code_task'] = "общая проверка кода"

text

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
----------------------------- ОБРАБОТЧИКИ ДЛЯ ОБУЧЕНИЯ PYTHON -----------------------------
async def learn_python_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
"""Обработчик команды /learn - начало или продолжение обучения Python"""
try:
conn = init_db()
user_id = update.effective_user.id
progress = get_user_python_progress(conn, user_id)

text

    # Получаем текущий уровень, модуль и урок
    level = progress[1]
    module = progress[2]
    lesson = progress[3]
    
    # Создаем клавиатуру для навигации по обучению
    keyboard = [
        [InlineKeyboardButton("📖 Продолжить обучение", callback_data=f"python_lesson_{level}_{module}_{lesson}")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="python_progress")],
        [InlineKeyboardButton("🔄 Начать сначала", callback_data="python_restart")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🐍 *Обучение Python с нуля* 🐍\n\n"
        "Добро пожаловать в интерактивный курс по Python! Здесь вы будете учиться программировать шаг за шагом.\n\n"
        "• Краткая теория\n"
        "• Практические задания\n"
        "• Постепенное усложнение\n"
        "• Обратная связь\n\n"
        "Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    conn.close()
except Exception as e:
    logger.error(f"Ошибка в команде learn_python: {e}")
    await update.message.reply_text(
        "Произошла ошибка при запуске обучения. Пожалуйста, попробуйте позже."
    )
async def handle_python_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE, level, module, lesson):
"""Показывает урок Python с теорией и практикой"""
try:
query = update.callback_query
conn = init_db()
user_id = query.from_user.id

text

    # Получаем данные урока
    lesson_data = PYTHON_COURSE[level]["modules"][module]["lessons"][lesson]
    
    # Формируем сообщение с теорией
    message = f"*{lesson_data['title']}*\n\n{lesson_data['theory']}"
    
    # Создаем клавиатуру с кнопками
    keyboard = [
        [InlineKeyboardButton("▶️ Практика", callback_data=f"python_practice_{level}_{module}_{lesson}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="python_back")]
    ]
    
    # Добавляем кнопку перехода к следующему уроку, если он есть
    lesson_num = int(lesson.split("_")[1])
    next_lesson = f"lesson_{lesson_num + 1}"
    
    if next_lesson in PYTHON_COURSE[level]["modules"][module]["lessons"]:
        keyboard[0].append(InlineKeyboardButton("➡️ Следующий урок", 
                                             callback_data=f"python_lesson_{level}_{module}_{next_lesson}"))
    else:
        # Проверяем, есть ли следующий модуль
        module_num = int(module.split("_")[1])
        next_module = f"module_{module_num + 1}"
        
        if next_module in PYTHON_COURSE[level]["modules"]:
            keyboard[0].append(InlineKeyboardButton("➡️ Следующий модуль", 
                                                 callback_data=f"python_lesson_{level}_{next_module}_lesson_1"))
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Обновляем прогресс пользователя
    update_user_python_progress(conn, user_id, level, module, lesson)
    
    # Отправляем сообщение с теорией
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    conn.close()
except Exception as e:
    logger.error(f"Ошибка при показе урока Python: {e}")
    await query.edit_message_text(
        "Произошла ошибка при загрузке урока. Пожалуйста, попробуйте позже.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="python_back")]])
    )
async def handle_python_practice(update: Update, context: ContextTypes.DEFAULT_TYPE, level, module, lesson):
"""Показывает практическое задание Python"""
try:
query = update.callback_query
conn = init_db()
user_id = query.from_user.id

text

    # Получаем данные урока
    lesson_data = PYTHON_COURSE[level]["modules"][module]["lessons"][lesson]
    practice_data = lesson_data["practice"]
    
    # Формируем сообщение с заданием
    message = f"*Практическое задание:*\n\n{practice_data['task']}"
    
    # Создаем клавиатуру в зависимости от типа задания
    keyboard = []
    
    if practice_data["type"] == "quiz":
        # Для теста с выбором варианта
        options = practice_data["options"]
        keyboard = [[InlineKeyboardButton(option, callback_data=f"python_answer_{level}_{module}_{lesson}_{i}")] 
                    for i, option in enumerate(options)]
    elif practice_data["type"] == "code":
        # Для задания с написанием кода
        context.user_data['waiting_for_python_code'] = True
        context.user_data['waiting_for_code'] = False
        context.user_data['python_task'] = {
            "level": level,
            "module": module,
            "lesson": lesson,
            "solution": practice_data["solution"]
        }
        message += "\n\n_Отправьте ваш код в следующем сообщении_"
    
    # Добавляем кнопку подсказки и возврата к теории
    hint_button = [InlineKeyboardButton("💡 Подсказка", callback_data=f"python_hint_{level}_{module}_{lesson}")]
    back_button = [InlineKeyboardButton("⬅️ Вернуться к теории", callback_data=f"python_lesson_{level}_{module}_{lesson}")]
    
    keyboard.append(hint_button)
    keyboard.append(back_button)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение с заданием
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    conn.close()
except Exception as e:
    logger.error(f"Ошибка при показе практики Python: {e}")
    await query.edit_message_text(
        "Произошла ошибка при загрузке задания. Пожалуйста, попробуйте позже.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="python_back")]])
    )
async def handle_python_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, level, module, lesson, answer_id):
"""Обрабатывает ответ на тест с выбором варианта"""
try:
query = update.callback_query
conn = init_db()
user_id = query.from_user.id

text

    # Получаем данные урока и правильный ответ
    lesson_data = PYTHON_COURSE[level]["modules"][module]["lessons"][lesson]
    practice_data = lesson_data["practice"]
    correct_answer = practice_data["correct"]
    
    # Проверяем ответ
    is_correct = int(answer_id) == correct_answer
    
    if is_correct:
        message = "✅ Правильно! Отличная работа!\n\n"
        
        # Добавляем очки и отмечаем урок как выполненный
        update_user_python_progress(conn, user_id, add_completed=True, add_points=10)
        
        # Проверяем, есть ли следующий урок
        lesson_num = int(lesson.split("_")[1])
        next_lesson = f"lesson_{lesson_num + 1}"
        
        if next_lesson in PYTHON_COURSE[level]["modules"][module]["lessons"]:
            message += f"Переходите к следующему уроку!"
            keyboard = [
                [InlineKeyboardButton("➡️ Следующий урок", 
                                   callback_data=f"python_lesson_{level}_{module}_{next_lesson}")],
                [InlineKeyboardButton("🔙 К списку уроков", callback_data="python_back")]
            ]
        else:
            # Проверяем, есть ли следующий модуль
            module_num = int(module.split("_")[1])
            next_module = f"module_{module_num + 1}"
            
            if next_module in PYTHON_COURSE[level]["modules"]:
                message += f"Вы завершили модуль! Переходите к следующему."
                keyboard = [
                    [InlineKeyboardButton("➡️ Следующий модуль", 
                                       callback_data=f"python_lesson_{level}_{next_module}_lesson_1")],
                    [InlineKeyboardButton("🔙 К списку уроков", callback_data="python_back")]
                ]
            else:
                message += f"Поздравляем! Вы завершили уровень!"
                keyboard = [
                    [InlineKeyboardButton("🎓 Завершить обучение", callback_data="python_complete")],
                    [InlineKeyboardButton("🔙 К списку уроков", callback_data="python_back")]
                ]
    else:
        message = "❌ Неправильно. Попробуйте еще раз.\n\n"
        message += f"Задание: {practice_data['task']}"
        
        # Создаем клавиатуру с вариантами ответов заново
        options = practice_data["options"]
        keyboard = [[InlineKeyboardButton(option, callback_data=f"python_answer_{level}_{module}_{lesson}_{i}")] 
                    for i, option in enumerate(options)]
        keyboard.append([InlineKeyboardButton("💡 Подсказка", callback_data=f"python_hint_{level}_{module}_{lesson}")])
        keyboard.append([InlineKeyboardButton("⬅️ Вернуться к теории", callback_data=f"python_lesson_{level}_{module}_{lesson}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем результат
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    conn.close()
except Exception as e:
    logger.error(f"Ошибка при обработке ответа Python: {e}")
    await query.edit_message_text(
        "Произошла ошибка при проверке ответа. Пожалуйста, попробуйте позже.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="python_back")]])
    )
async def handle_python_hint(update: Update, context: ContextTypes.DEFAULT_TYPE, level, module, lesson):
"""Показывает подсказку для задания"""
try:
query = update.callback_query

text

    # Получаем данные урока и подсказку
    lesson_data = PYTHON_COURSE[level]["modules"][module]["lessons"][lesson]
    practice_data = lesson_data["practice"]
    hint = practice_data.get("hint", "Подсказка недоступна для этого задания.")
    
    # Формируем сообщение с подсказкой
    message = f"*Подсказка:*\n\n{hint}\n\n*Задание:*\n\n{practice_data['task']}"
    
    # Создаем клавиатуру для возврата к заданию
    keyboard = [
        [InlineKeyboardButton("⬅️ Вернуться к заданию", callback_data=f"python_practice_{level}_{module}_{lesson}")],
        [InlineKeyboardButton("⬅️ Вернуться к теории", callback_data=f"python_lesson_{level}_{module}_{lesson}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем подсказку
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
except Exception as e:
    logger.error(f"Ошибка при показе подсказки Python: {e}")
    await query.edit_message_text(
        "Произошла ошибка при загрузке подсказки. Пожалуйста, попробуйте позже.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="python_back")]])
    )
async def handle_python_code_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
"""Проверяет код, отправленный пользователем"""
try:
if not context.user_data.get('waiting_for_python_code'):
return False

text

    conn = init_db()
    user_id = update.effective_user.id
    code = update.message.text
    
    task_info = context.user_data.get('python_task', {})
    level = task_info.get("level")
    module = task_info.get("module")
    lesson = task_info.get("lesson")
    solution = task_info.get("solution")
    
    if not all([level, module, lesson, solution]):
        await update.message.reply_text(
            "Произошла ошибка при проверке кода. Пожалуйста, попробуйте снова."
        )
        return True
    
    # Получаем данные урока
    lesson_data = PYTHON_COURSE[level]["modules"][module]["lessons"][lesson]
    
    # Очищаем состояние ожидания кода
    context.user_data['waiting_for_python_code'] = False
    context.user_data['python_task'] = {}
    
    # Проверяем код
    # Здесь мы используем упрощенную проверку - сравниваем с ожидаемым решением
    # В реальном боте можно использовать более сложную логику или вызывать API для проверки
    
    # Нормализуем код (убираем лишние пробелы и т.д.)
    normalized_code = code.strip().replace(" ", "").replace("\n", "")
    normalized_solution = solution.strip().replace(" ", "").replace("\n", "")
    
    is_correct = normalized_code == normalized_solution
    
    if is_correct:
        message = "✅ Правильно! Ваш код работает корректно.\n\n"
        
        # Добавляем очки и отмечаем урок как выполненный
        update_user_python_progress(conn, user_id, add_completed=True, add_points=15)
        
        # Проверяем, есть ли следующий урок
        lesson_num = int(lesson.split("_")[1])
        next_lesson = f"lesson_{lesson_num + 1}"
        
        if next_lesson in PYTHON_COURSE[level]["modules"][module]["lessons"]:
            message += f"Переходите к следующему уроку!"
            keyboard = [
                [InlineKeyboardButton("➡️ Следующий урок", 
                                   callback_data=f"python_lesson_{level}_{module}_{next_lesson}")],
                [InlineKeyboardButton("🔙 К списку уроков", callback_data="python_back")]
            ]
        else:
            # Проверяем, есть ли следующий модуль
            module_num = int(module.split("_")[1])
            next_module = f"module_{module_num + 1}"
            
            if next_module in PYTHON_COURSE[level]["modules"]:
                message += f"Вы завершили модуль! Переходите к следующему."
                keyboard = [
                    [InlineKeyboardButton("➡️ Следующий модуль", 
                                       callback_data=f"python_lesson_{level}_{next_module}_lesson_1")],
                    [InlineKeyboardButton("🔙 К списку уроков", callback_data="python_back")]
                ]
            else:
                message += f"Поздравляем! Вы завершили уровень!"
                keyboard = [
                    [InlineKeyboardButton("🎓 Завершить обучение", callback_data="python_complete")],
                    [InlineKeyboardButton("🔙 К списку уроков", callback_data="python_back")]
                ]
    else:
        # Если код неверный, анализируем его и даем обратную связь
        feedback = await check_code(code, lesson_data["practice"]["task"])
        
        message = f"❌ Ваш код не совсем соответствует ожидаемому решению.\n\n{feedback}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"python_practice_{level}_{module}_{lesson}")],
            [InlineKeyboardButton("💡 Подсказка", callback_data=f"python_hint_{level}_{module}_{lesson}")],
            [InlineKeyboardButton("⬅️ Вернуться к теории", callback_data=f"python_lesson_{level}_{module}_{lesson}")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем результат
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    conn.close()
    return True
except Exception as e:
    logger.error(f"Ошибка при проверке кода Python: {e}")
    await update.message.reply_text(
        "Произошла ошибка при проверке кода. Пожалуйста, попробуйте позже.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К обучению", callback_data="python_back")]])
    )
    return True
----------------------------- ОБРАБОТЧИКИ СООБЩЕНИЙ -----------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
"""Обработчик обычных текстовых сообщений от пользователя"""
try:
# Проверяем, ожидаем ли мы код для проверки в модуле обучения Python
if context.user_data.get('waiting_for_python_code'):
is_handled = await handle_python_code_submission(update, context)
if is_handled:
return

text

    # Продолжаем обычную обработку сообщений, если это не код для Python
    conn = init_db()
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Проверяем, ожидаем ли мы код от пользователя для обычной проверки
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
----------------------------- ОБРАБОТЧИКИ КНОПОК -----------------------------
async def handle_python_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
"""Обрабатывает нажатия кнопок в модуле обучения Python"""
query = update.callback_query
callback_data = query.data

text

try:
    # Обработка кнопки возврата к меню обучения
    if callback_data == "python_back":
        await learn_python_command(update, context)
        return
    
    # Обработка кнопки показа урока
    if callback_data.startswith("python_lesson_"):
        parts = callback_data.split("_")
        level = f"{parts[2]}_{parts[3]}"
        module = f"{parts[4]}_{parts[5]}"
        lesson = f"{parts[6]}_{parts[7]}"
        await handle_python_lesson(update, context, level, module, lesson)
        return
    
    # Обработка кнопки показа практики
    if callback_data.startswith("python_practice_"):
        parts = callback_data.split("_")
        level = f"{parts[2]}_{parts[3]}"
        module = f"{parts[4]}_{parts[5]}"
        lesson = f"{parts[6]}_{parts[7]}"
        await handle_python_practice(update, context, level, module, lesson)
        return
    
    # Обработка кнопки ответа на тест
    if callback_data.startswith("python_answer_"):
        parts = callback_data.split("_")
        level = f"{parts[2]}_{parts[3]}"
        module = f"{parts[4]}_{parts[5]}"
        lesson = f"{parts[6]}_{parts[7]}"
        answer_id = parts[8]
        await handle_python_answer(update, context, level, module, lesson, answer_id)
        return
    
    # Обработка кнопки подсказки
    if callback_data.startswith("python_hint_"):
        parts = callback_data.split("_")
        level = f"{parts[2]}_{parts[3]}"
        module = f"{parts[4]}_{parts[5]}"
        lesson = f"{parts[6]}_{parts[7]}"
        await handle_python_hint(update, context, level, module, lesson)
        return
    
    # Обработка кнопки просмотра прогресса
    if callback_data == "python_progress":
        conn = init_db()
        user_id = query.from_user.id
        progress = get_user_python_progress(conn, user_id)
        
        completed_lessons = json.loads(progress[4])
        points = progress[5]
        
        message = "*Ваш прогресс в изучении Python*\n\n"
        message += f"📊 Очки: {points}\n"
        message += f"📚 Выполнено уроков: {len(completed_lessons)}\n\n"
        
        # Показываем прогресс по уровням и модулям
        for level_id, level_data in PYTHON_COURSE.items():
            level_completed = 0
            level_total = 0
            
            message += f"*{level_data['title']}*\n"
            
            for module_id, module_data in level_data["modules"].items():
                module_completed = 0
                module_total = len(module_data["lessons"])
                level_total += module_total
                
                for lesson_id in module_data["lessons"]:
                    lesson_key = f"{level_id}_{module_id}_{lesson_id}"
                    if lesson_key in completed_lessons:
                        module_completed += 1
                        level_completed += 1
                
                progress_percent = int(module_completed / module_total * 100) if module_total > 0 else 0
                progress_bar = "▓" * (progress_percent // 10) + "░" * (10 - progress_percent // 10)
                
                message += f"  └ {module_data['title']}: {module_completed}/{module_total} [{progress_bar}] {progress_percent}%\n"
            
            level_percent = int(level_completed / level_total * 100) if level_total > 0 else 0
            message += f"  Всего: {level_completed}/{level_total} ({level_percent}%)\n\n"
        
        # Добавляем кнопку возврата
        keyboard = [
            [InlineKeyboardButton("📖 Продолжить обучение", 
                               callback_data=f"python_lesson_{progress[1]}_{progress[2]}_{progress[3]}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="python_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        conn.close()
        return
    
    # Обработка кнопки перезапуска обучения
    if callback_data == "python_restart":
        conn = init_db()
        user_id = query.from_user.id
        
        # Подтверждение перезапуска
        message = "Вы уверены, что хотите начать обучение сначала? Весь ваш прогресс будет сброшен."
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, начать сначала", callback_data="python_restart_confirm")],
            [InlineKeyboardButton("❌ Нет, отменить", callback_data="python_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
        
        conn.close()
        return
    
    # Обработка подтверждения перезапуска
    if callback_data == "python_restart_confirm":
        conn = init_db()
        user_id = query.from_user.id
        
        # Сбрасываем прогресс
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE python_progress SET current_level = ?, current_module = ?, current_lesson = ?, completed_lessons = ?, points = ?, last_activity = ? WHERE user_id = ?",
            ("level_1", "module_1", "lesson_1", json.dumps([]), 0, datetime.datetime.now(), user_id)
        )
        conn.commit()
        
        message = "✅ Ваш прогресс успешно сброшен. Вы начинаете обучение с первого урока."
        
        keyboard = [
            [InlineKeyboardButton("📖 Начать обучение", callback_data="python_lesson_level_1_module_1_lesson_1")],
            [InlineKeyboardButton("🔙 Назад", callback_data="python_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
        
        conn.close()
        return
    
    # Обработка завершения обучения
    if callback_data == "python_complete":
        conn = init_db()
        user_id = query.from_user.id
        progress = get_user_python_progress(conn, user_id)
        
        points = progress[5]
        
        message = "🎉 *Поздравляем с завершением обучения!* 🎉\n\n"
        message += f"Вы заработали {points} очков и многому научились в процессе.\n\n"
        message += "Продолжайте практиковаться и развивать свои навыки программирования!\n\n"
        message += "Что бы вы хотели изучить дальше?"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить курс", callback_data="python_restart")],
            [InlineKeyboardButton("🤖 Вернуться к боту", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        conn.close()
        return

except Exception as e:
    logger.error(f"Ошибка при обработке кнопок Python: {e}")
    await query.edit_message_text(
        "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="python_back")]])
    )
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
"""Обработчик нажатий на кнопки интерактивного меню"""
try:
query = update.callback_query
await query.answer() # Подтверждаем нажатие кнопки

text

    callback_data = query.data
    
    # Перенаправляем кнопки обучения Python в отдельный обработчик
    if callback_data.startswith("python_"):
        await handle_python_buttons(update, context)
        return
    
    conn = init_db()
    user_id = query.from_user.id
    
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
             InlineKeyboardButton("🌱 Образ жизни", callback_data="lifestyle")],
            [InlineKeyboardButton("🐍 Изучить Python", callback_data="python_back")]
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
except Exception as e:
    logger.error(f"Ошибка в обработчике button_handler: {e}")
    try:
        await query.edit_message_text(
            "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте снова или используйте команду /start."
        )
    except:
        pass
----------------------------- ОСНОВНАЯ ФУНКЦИЯ -----------------------------
def main():
"""Основная функция для запуска бота"""
try:
# Инициализация базы данных
conn = init_db()
conn.close()

text

    # Создание и настройка приложения
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("challenge", challenge_command))
    application.add_handler(CommandHandler("challenges", challenges_command))
    application.add_handler(CommandHandler("workout", workout_command))
    application.add_handler(CommandHandler("code", code_command))
    application.add_handler(CommandHandler("learn", learn_python_command))
    
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
----------------------------- ЗАПУСК БОТА -----------------------------
if name == "main":
main()
