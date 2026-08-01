import os
import telebot
from telebot import types
import sqlite3
from datetime import datetime

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

# ================= ССЫЛКИ =================
LINK_BLACK = "https://tbank.ru/baf/6cDotN3sm66"
LINK_BUSINESS = "https://tbank.ru/baf/4fWsjkGRCpn"
LINK_INVEST = "https://tbank.ru/baf/4Nha2vM22nm"
LINK_ALL = "https://tbank.ru/baf/58KGejb8KDQ"

ADMIN_ID = 8896790430

# ================= БАЗА ДАННЫХ =================
def init_db():
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            first_seen TEXT,
            last_seen TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            button TEXT,
            click_date TEXT,
            click_time TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def save_user(user):
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or "нет"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    cur.execute("""
        INSERT INTO users (user_id, username, full_name, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name,
            last_seen = excluded.last_seen
    """, (user.id, username, full_name, now, now))
    
    conn.commit()
    conn.close()

def add_click(user_id, button):
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    now = datetime.now()
    cur.execute("""
        INSERT INTO clicks (user_id, button, click_date, click_time)
        VALUES (?, ?, ?, ?)
    """, (user_id, button, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_users_stats():
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    
    cur.execute("SELECT user_id, username, full_name, first_seen, last_seen FROM users ORDER BY last_seen DESC")
    users = cur.fetchall()
    
    result = []
    for user in users:
        user_id, username, full_name, first_seen, last_seen = user
        cur.execute("SELECT button, COUNT(*) FROM clicks WHERE user_id = ? GROUP BY button", (user_id,))
        clicks = dict(cur.fetchall())
        
        result.append({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "first_seen": first_seen,
            "last_seen": last_seen,
            "clicks": clicks
        })
    
    conn.close()
    return result

def get_user_stats(user_id):
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    
    cur.execute("SELECT username, full_name, first_seen, last_seen FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()
    
    if not user:
        conn.close()
        return None
    
    cur.execute("SELECT button, COUNT(*) FROM clicks WHERE user_id = ? GROUP BY button", (user_id,))
    clicks = dict(cur.fetchall())
    
    conn.close()
    return {
        "user_id": user_id,
        "username": user[0],
        "full_name": user[1],
        "first_seen": user[2],
        "last_seen": user[3],
        "clicks": clicks
    }

init_db()

# ================= КЛАВИАТУРА =================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("💳 Карта Black + 500 ₽"))
    markup.add(types.KeyboardButton("💼 Бизнес-счёт"))
    markup.add(types.KeyboardButton("📈 Счёт для инвестиций"))
    markup.add(types.KeyboardButton("🔍 Выбери продукт сам"))
    markup.add(types.KeyboardButton("📋 Подробнее о продуктах"))
    markup.add(types.KeyboardButton("🔥 Почему это выгодно"))
    markup.add(types.KeyboardButton("⚠️ Важно"))
    return markup

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user)
    add_click(message.from_user.id, "start")
    
    text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Здесь можно быстро оформить выгодные продукты Т-Банка.\n\n"
        "Выбирай, что тебе интересно 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard(), parse_mode="HTML")

# ================= АДМИН КОМАНДЫ =================
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = get_all_users_stats()
    total = len(users)
    
    text = (
        f"📊 <b>Общая статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n\n"
        f"Команды:\n"
        f"/users — список всех людей\n"
        f"/user ID — статистика по человеку"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['users'])
def users_list(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = get_all_users_stats()
    
    if not users:
        bot.send_message(message.chat.id, "Пока никто не заходил.")
        return
    
    text = "👥 <b>Список людей:</b>\n\n"
    
    for u in users:
        clicks = u['clicks']
        text += f"👤 <b>{u['full_name']}</b>\n"
        text += f"ID: <code>{u['user_id']}</code>\n"
        text += f"@{u['username']}\n"
        text += f"Последний раз: {u['last_seen']}\n"
        text += f"Нажатия: start {clicks.get('start', 0)} | black {clicks.get('black', 0)} | business {clicks.get('business', 0)} | invest {clicks.get('invest', 0)}\n"
        text += "————————————\n"
        
        if len(text) > 3500:
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            text = ""
    
    if text:
        bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['user'])
def user_info(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
    except:
        bot.send_message(message.chat.id, "Использование:\n<code>/user 123456789</code>", parse_mode="HTML")
        return
    
    u = get_user_stats(user_id)
    
    if not u:
        bot.send_message(message.chat.id, "Пользователь не найден.")
        return
    
    clicks = u['clicks']
    
    text = (
        f"👤 <b>{u['full_name']}</b>\n"
        f"ID: <code>{u['user_id']}</code>\n"
        f"Username: @{u['username']}\n"
        f"Первый раз: {u['first_seen']}\n"
        f"Последний раз: {u['last_seen']}\n\n"
        f"<b>Нажатия кнопок:</b>\n"
        f"• /start — {clicks.get('start', 0)}\n"
        f"• Карта Black — {clicks.get('black', 0)}\n"
        f"• Бизнес-счёт — {clicks.get('business', 0)}\n"
        f"• Инвестиции — {clicks.get('invest', 0)}\n"
        f"• Выбери продукт — {clicks.get('all', 0)}\n"
        f"• Подробнее — {clicks.get('info', 0)}\n"
        f"• Почему выгодно — {clicks.get('why', 0)}\n"
        f"• Важно — {clicks.get('important', 0)}"
    )
    
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ================= ОБРАБОТКА КНОПОК =================
@bot.message_handler(func=lambda message: True)
def handle(message):
    save_user(message.from_user)
    text = message.text.lower()
    user_id = message.from_user.id

    if "карта" in text or "black" in text or "500" in text:
        add_click(user_id, "black")
        desc = (
            "💳 <b>Дебетовая карта T-Bank Black</b>\n\n"
            "• Кэшбэк до 30%\n"
            "• 500 ₽ в подарок\n"
            "• Часто бесплатное обслуживание\n"
            "• Бесплатные переводы\n"
            "• Доставка карты домой"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 Оформить карту + 500 ₽", url=LINK_BLACK))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    elif "бизнес" in text:
        add_click(user_id, "business")
        desc = (
            "💼 <b>Бизнес-счёт Т-Банка</b>\n\n"
            "• Открытие онлайн за несколько минут\n"
            "• Удобное приложение для бизнеса\n"
            "• Бесплатные переводы и платежи\n"
            "• Подходит для ИП и ООО"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💼 Открыть бизнес-счёт", url=LINK_BUSINESS))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    elif "инвест" in text:
        add_click(user_id, "invest")
        desc = (
            "📈 <b>Счёт для инвестиций</b>\n\n"
            "• Открытие брокерского счёта онлайн\n"
            "• Акции, облигации, ETF\n"
            "• Можно начать с небольшой суммы\n"
            "• Удобное приложение"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📈 Открыть инвестиционный счёт", url=LINK_INVEST))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    elif "выбери" in text or "продукт сам" in text:
        add_click(user_id, "all")
        desc = (
            "🔍 <b>Выбери продукт сам</b>\n\n"
            "На странице доступны все продукты Т-Банка:\n"
            "карты, бизнес-счёт, инвестиции и другое."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔍 Выбрать продукт", url=LINK_ALL))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    elif "подробнее" in text:
        add_click(user_id, "info")
        text_info = (
            "📋 <b>Кратко о продуктах:</b>\n\n"
            "💳 Карта Black — кэшбэк + 500 ₽\n"
            "💼 Бизнес-счёт — для ИП и ООО\n"
            "📈 Инвестиции — акции и облигации\n"
            "🔍 Выбери сам — все продукты банка"
        )
        bot.send_message(message.chat.id, text_info, parse_mode="HTML")

    elif "выгодно" in text:
        add_click(user_id, "why")
        bot.send_message(message.chat.id, "🔥 Всё оформляется онлайн, часто есть бонусы и удобные приложения.")

    elif "важно" in text:
        add_click(user_id, "important")
        text_important = (
            "⚠️ <b>Важно знать</b>\n\n"
            "Чтобы получить бонус, нужно:\n\n"
            "1. Оформить продукт <b>по ссылке из бота</b>\n"
            "2. Выполнить условия акции (обычно покупка или пополнение)\n"
            "3. Дождаться начисления бонуса\n\n"
            "Если условия не выполнить — бонус может не прийти."
        )
        bot.send_message(message.chat.id, text_important, parse_mode="HTML")

    else:
        bot.send_message(message.chat.id, "Используй кнопки меню 👇", reply_markup=main_keyboard())

print("✅ Бот запущен!")
bot.infinity_polling()
