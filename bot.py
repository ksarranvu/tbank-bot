import os
import telebot
from telebot import types
import sqlite3
from datetime import datetime, date, timedelta

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

# ================= ССЫЛКИ =================
LINK_BLACK = "https://tbank.ru/baf/6cDotN3sm66"
LINK_BUSINESS = "https://tbank.ru/baf/4fWsjkGRCpn"
LINK_INVEST = "https://tbank.ru/baf/4Nha2vM22nm"
LINK_ALL = "https://tbank.ru/baf/58KGejb8KDQ"

# ================= БАЗА ДАННЫХ =================
def init_db():
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_seen TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            button TEXT,
            click_date TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, first_seen) VALUES (?, ?)",
                (user_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def add_click(user_id, button):
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO clicks (user_id, button, click_date) VALUES (?, ?, ?)",
                (user_id, button, date.today().isoformat()))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    
    today = date.today().isoformat()
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM clicks WHERE click_date = ?", (today,))
    today_users = cur.fetchone()[0]
    
    cur.execute("SELECT button, COUNT(*) FROM clicks GROUP BY button")
    all_clicks = dict(cur.fetchall())
    
    cur.execute("SELECT button, COUNT(*) FROM clicks WHERE click_date = ? GROUP BY button", (today,))
    today_clicks = dict(cur.fetchall())
    
    last_7_days = []
    for i in range(6, -1, -1):
        day = (date.today() - timedelta(days=i)).isoformat()
        cur.execute("SELECT COUNT(DISTINCT user_id) FROM clicks WHERE click_date = ?", (day,))
        users_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM clicks WHERE click_date = ?", (day,))
        clicks_count = cur.fetchone()[0]
        last_7_days.append((day, users_count, clicks_count))
    
    conn.close()
    return total_users, today_users, all_clicks, today_clicks, last_7_days

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
    return markup

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)
    add_click(message.from_user.id, "start")
    
    text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Здесь можно быстро оформить выгодные продукты Т-Банка.\n\n"
        "Выбирай, что тебе интересно 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard(), parse_mode="HTML")

# ================= СТАТИСТИКА =================
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != 8896790430:
        return
    
    total_users, today_users, all_clicks, today_clicks, last_7_days = get_stats()
    
    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего уникальных пользователей: <b>{total_users}</b>\n"
        f"📅 Зашли сегодня: <b>{today_users}</b>\n\n"
        f"<b>🔘 Нажатия за всё время:</b>\n"
        f"• /start — {all_clicks.get('start', 0)}\n"
        f"• Карта Black — {all_clicks.get('black', 0)}\n"
        f"• Бизнес-счёт — {all_clicks.get('business', 0)}\n"
        f"• Инвестиции — {all_clicks.get('invest', 0)}\n"
        f"• Выбери продукт — {all_clicks.get('all', 0)}\n"
        f"• Подробнее — {all_clicks.get('info', 0)}\n"
        f"• Почему выгодно — {all_clicks.get('why', 0)}\n\n"
        f"<b>📅 Нажатия сегодня:</b>\n"
        f"• /start — {today_clicks.get('start', 0)}\n"
        f"• Карта Black — {today_clicks.get('black', 0)}\n"
        f"• Бизнес-счёт — {today_clicks.get('business', 0)}\n"
        f"• Инвестиции — {today_clicks.get('invest', 0)}\n"
        f"• Выбери продукт — {today_clicks.get('all', 0)}\n"
        f"• Подробнее — {today_clicks.get('info', 0)}\n"
        f"• Почему выгодно — {today_clicks.get('why', 0)}\n\n"
        f"<b>📈 Последние 7 дней:</b>\n"
    )
    
    for day, users_count, clicks_count in last_7_days:
        text += f"• {day}: {users_count} чел. / {clicks_count} нажатий\n"
    
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ================= ОБРАБОТКА КНОПОК =================
@bot.message_handler(func=lambda message: True)
def handle(message):
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

    else:
        bot.send_message(message.chat.id, "Используй кнопки меню 👇", reply_markup=main_keyboard())

print("✅ Бот запущен!")
bot.infinity_polling()
