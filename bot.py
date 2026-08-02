import os
import telebot
from telebot import types
import sqlite3
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 8896790430
API_KEY = os.getenv("API_KEY", "LOX22899")  # свой ключ в Variables

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

app = Flask(__name__)

LINK_BLACK = "https://tbank.ru/baf/6cDotN3sm66"
LINK_BUSINESS = "https://tbank.ru/baf/4fWsjkGRCpn"
LINK_INVEST = "https://tbank.ru/baf/4Nha2vM22nm"
LINK_ALL = "https://tbank.ru/baf/58KGejb8KDQ"

def init_db():
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            first_seen TEXT,
            last_seen TEXT,
            from_staff_id INTEGER DEFAULT NULL
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff_referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER,
            client_id INTEGER,
            client_name TEXT,
            status TEXT DEFAULT 'started',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user(user, from_staff_id=None):
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or "нет"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user.id,))
    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO users (user_id, username, full_name, first_seen, last_seen, from_staff_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user.id, username, full_name, now, now, from_staff_id))
        if from_staff_id:
            cur.execute("""
                INSERT INTO staff_referrals (staff_id, client_id, client_name, status, created_at)
                VALUES (?, ?, ?, 'started', ?)
            """, (from_staff_id, user.id, full_name, now))
    else:
        cur.execute("""
            UPDATE users SET username=?, full_name=?, last_seen=? WHERE user_id=?
        """, (username, full_name, now, user.id))
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

init_db()

# ================= API =================
def check_key():
    return request.args.get("key") == API_KEY

@app.route("/api/stats")
def api_stats():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT button, COUNT(*) FROM clicks GROUP BY button")
    clicks = dict(cur.fetchall())
    cur.execute("SELECT COUNT(*) FROM staff_referrals")
    total_refs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM staff_referrals WHERE status='completed'")
    completed_refs = cur.fetchone()[0]
    conn.close()
    return jsonify({
        "total_users": total_users,
        "clicks": clicks,
        "total_refs": total_refs,
        "completed_refs": completed_refs
    })

@app.route("/api/users")
def api_users():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, username, full_name, first_seen, last_seen, from_staff_id
        FROM users ORDER BY last_seen DESC LIMIT 100
    """)
    rows = cur.fetchall()
    users = []
    for r in rows:
        cur.execute("SELECT button, COUNT(*) FROM clicks WHERE user_id=? GROUP BY button", (r[0],))
        clicks = dict(cur.fetchall())
        users.append({
            "user_id": r[0],
            "username": r[1],
            "full_name": r[2],
            "first_seen": r[3],
            "last_seen": r[4],
            "from_staff_id": r[5],
            "clicks": clicks
        })
    conn.close()
    return jsonify({"users": users})

@app.route("/api/staff")
def api_staff():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT staff_id,
               COUNT(*) as total,
               SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed
        FROM staff_referrals
        GROUP BY staff_id
    """)
    rows = cur.fetchall()
    conn.close()
    return jsonify({
        "staff": [{"staff_id": r[0], "total": r[1], "completed": r[2]} for r in rows]
    })

# ================= BOT =================
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

@bot.message_handler(commands=['start'])
def start(message):
    from_staff_id = None
    if message.text and len(message.text.split()) > 1:
        param = message.text.split()[1]
        if param.startswith("emp_"):
            try:
                from_staff_id = int(param.replace("emp_", ""))
            except:
                pass
    save_user(message.from_user, from_staff_id)
    add_click(message.from_user.id, "start")
    text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Здесь можно быстро оформить выгодные продукты Т-Банка.\n\n"
        "Выбирай, что тебе интересно 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard(), parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle(message):
    save_user(message.from_user)
    text = (message.text or "").lower()
    user_id = message.from_user.id

    if "карта" in text or "black" in text or "500" in text:
        add_click(user_id, "black")
        desc = "💳 <b>Дебетовая карта T-Bank Black</b>\n\n• Кэшбэк до 30%\n• 500 ₽ в подарок\n• Часто бесплатное обслуживание\n• Доставка карты домой"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 Оформить карту + 500 ₽", url=LINK_BLACK))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")
    elif "бизнес" in text:
        add_click(user_id, "business")
        desc = "💼 <b>Бизнес-счёт Т-Банка</b>\n\n• Открытие онлайн\n• Удобное приложение\n• Для ИП и ООО"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💼 Открыть бизнес-счёт", url=LINK_BUSINESS))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")
    elif "инвест" in text:
        add_click(user_id, "invest")
        desc = "📈 <b>Счёт для инвестиций</b>\n\n• Акции, облигации, ETF\n• Можно начать с небольшой суммы"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📈 Открыть счёт", url=LINK_INVEST))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")
    elif "выбери" in text or "продукт сам" in text:
        add_click(user_id, "all")
        desc = "🔍 <b>Выбери продукт сам</b>\n\nВсе продукты Т-Банка в одном месте."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔍 Выбрать", url=LINK_ALL))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")
    elif "подробнее" in text:
        add_click(user_id, "info")
        bot.send_message(message.chat.id, "📋 Карта Black, бизнес-счёт, инвестиции — всё в меню.", parse_mode="HTML")
    elif "выгодно" in text:
        add_click(user_id, "why")
        bot.send_message(message.chat.id, "🔥 Оформление онлайн, бонусы и удобные приложения.")
    elif "важно" in text:
        add_click(user_id, "important")
        bot.send_message(message.chat.id, "⚠️ Оформляй по ссылке из бота и выполни условия акции.", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "Используй кнопки меню 👇", reply_markup=main_keyboard())

def run_api():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_api, daemon=True).start()
    print("✅ Основной бот + API запущены")
    bot.infinity_polling()
