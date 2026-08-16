import os
import telebot
from telebot import types
import sqlite3
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 8896790430
API_KEY = os.getenv("API_KEY", "LOX22899")

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

app = Flask(__name__)
CORS(app)

LINK_BLACK = "https://tbank.ru/baf/6cDotN3sm66"
LINK_BUSINESS = "https://tbank.ru/baf/4fWsjkGRCpn"
LINK_INVEST = "https://tbank.ru/baf/4Nha2vM22nm"
LINK_ALL = "https://tbank.ru/baf/58KGejb8KDQ"

# ===================== DB =====================
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff_members (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            first_seen TEXT,
            last_seen TEXT
        )
    """)
    conn.commit()
    conn.close()

def register_staff_member(user_id, username="нет", full_name="Без имени"):
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
        INSERT INTO staff_members (user_id, username, full_name, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            full_name=excluded.full_name,
            last_seen=excluded.last_seen
    """, (int(user_id), username, full_name, now, now))
    conn.commit()
    conn.close()

def save_user(user, from_staff_id=None):
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
    username = user.username or "нет"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cur.execute("SELECT user_id, from_staff_id FROM users WHERE user_id = ?", (user.id,))
    row = cur.fetchone()

    if not row:
        cur.execute("""
            INSERT INTO users (user_id, username, full_name, first_seen, last_seen, from_staff_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user.id, username, full_name, now, now, from_staff_id))
        if from_staff_id:
            cur.execute("""
                INSERT INTO staff_referrals (staff_id, client_id, client_name, status, created_at)
                VALUES (?, ?, ?, 'started', ?)
            """, (from_staff_id, user.id, full_name, now))
            try:
                bot.send_message(
                    ADMIN_ID,
                    f"🆕 Новый переход\nСотрудник: <code>{from_staff_id}</code>\n"
                    f"Клиент: <b>{full_name}</b>\n@{username}\nID: <code>{user.id}</code>",
                    parse_mode="HTML"
                )
            except:
                pass
    else:
        cur.execute("""
            UPDATE users SET username=?, full_name=?, last_seen=? WHERE user_id=?
        """, (username, full_name, now, user.id))
        old_staff = row[1]
        if from_staff_id and not old_staff:
            cur.execute("UPDATE users SET from_staff_id=? WHERE user_id=?", (from_staff_id, user.id))
            cur.execute("""
                INSERT INTO staff_referrals (staff_id, client_id, client_name, status, created_at)
                VALUES (?, ?, ?, 'started', ?)
            """, (from_staff_id, user.id, full_name, now))

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

# ===================== API =====================
def check_key():
    return request.args.get("key") == API_KEY

@app.route("/")
def home():
    return "Main bot API OK"

@app.route("/api/register_staff", methods=["GET", "POST"])
def api_register_staff():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    data = request.json if request.is_json else {}
    user_id = request.args.get("user_id") or data.get("user_id")
    username = request.args.get("username") or data.get("username") or "нет"
    full_name = request.args.get("full_name") or data.get("full_name") or "Без имени"
    if not user_id:
        return jsonify({"error": "no user_id"}), 400
    try:
        user_id = int(user_id)
    except:
        return jsonify({"error": "bad user_id"}), 400
    register_staff_member(user_id, username, full_name)
    return jsonify({"ok": True, "user_id": user_id})

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
    cur.execute("SELECT COUNT(*) FROM staff_members")
    total_staff = cur.fetchone()[0]
    conn.close()
    return jsonify({
        "total_users": total_users,
        "total_staff": total_staff,
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
        FROM users ORDER BY last_seen DESC LIMIT 150
    """)
    rows = cur.fetchall()
    users = []
    for r in rows:
        cur.execute("SELECT button, COUNT(*) FROM clicks WHERE user_id=? GROUP BY button", (r[0],))
        users.append({
            "user_id": r[0],
            "username": r[1],
            "full_name": r[2],
            "first_seen": r[3],
            "last_seen": r[4],
            "from_staff_id": r[5],
            "clicks": dict(cur.fetchall())
        })
    conn.close()
    return jsonify({"users": users})

@app.route("/api/staff")
def api_staff():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, full_name FROM staff_members")
    members = {r[0]: {"username": r[1], "full_name": r[2]} for r in cur.fetchall()}
    cur.execute("""
        SELECT staff_id,
               COUNT(*) as total,
               SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed
        FROM staff_referrals
        GROUP BY staff_id
    """)
    refs = {r[0]: {"total": r[1], "completed": r[2]} for r in cur.fetchall()}
    conn.close()
    result = []
    for uid in set(members.keys()) | set(refs.keys()):
        info = members.get(uid, {})
        st = refs.get(uid, {})
        result.append({
            "staff_id": uid,
            "user_id": uid,
            "username": info.get("username", "нет"),
            "full_name": info.get("full_name", f"ID {uid}"),
            "total": int(st.get("total", 0)),
            "completed": int(st.get("completed", 0))
        })
    result.sort(key=lambda x: x["total"], reverse=True)
    return jsonify({"staff": result})

# ===== ADMIN API FOR WEBSITE =====
@app.route("/api/admin/overview")
def api_admin_overview():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM staff_members")
    total_staff = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM staff_referrals")
    total_refs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM staff_referrals WHERE status='completed'")
    completed_refs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM clicks")
    total_clicks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE first_seen LIKE ?", (today + "%",))
    today_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM clicks WHERE click_date=?", (today,))
    today_clicks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM staff_referrals WHERE created_at LIKE ?", (today + "%",))
    today_refs = cur.fetchone()[0]
    cur.execute("SELECT button, COUNT(*) c FROM clicks GROUP BY button ORDER BY c DESC")
    top_buttons = [{"button": b, "count": c} for b, c in cur.fetchall()]
    conn.close()

    return jsonify({
        "total_users": total_users,
        "total_staff": total_staff,
        "total_refs": total_refs,
        "completed_refs": completed_refs,
        "total_clicks": total_clicks,
        "today_users": today_users,
        "today_clicks": today_clicks,
        "today_refs": today_refs,
        "top_buttons": top_buttons
    })

@app.route("/api/admin/users")
def api_admin_users():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    q = (request.args.get("q") or "").strip().lower()
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    if q:
        cur.execute("""
            SELECT user_id, username, full_name, first_seen, last_seen, from_staff_id
            FROM users
            WHERE lower(full_name) LIKE ? OR lower(username) LIKE ? OR cast(user_id as text) LIKE ?
            ORDER BY last_seen DESC LIMIT 100
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("""
            SELECT user_id, username, full_name, first_seen, last_seen, from_staff_id
            FROM users ORDER BY last_seen DESC LIMIT 100
        """)
    rows = cur.fetchall()
    users = []
    for r in rows:
        cur.execute("SELECT button, COUNT(*) FROM clicks WHERE user_id=? GROUP BY button", (r[0],))
        users.append({
            "user_id": r[0],
            "username": r[1],
            "full_name": r[2],
            "first_seen": r[3],
            "last_seen": r[4],
            "from_staff_id": r[5],
            "clicks": dict(cur.fetchall())
        })
    conn.close()
    return jsonify({"users": users})

@app.route("/api/admin/staff")
def api_admin_staff():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, full_name, first_seen, last_seen FROM staff_members")
    members = {
        r[0]: {
            "username": r[1],
            "full_name": r[2],
            "first_seen": r[3],
            "last_seen": r[4]
        } for r in cur.fetchall()
    }
    cur.execute("""
        SELECT staff_id,
               COUNT(*) as total,
               SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed
        FROM staff_referrals
        GROUP BY staff_id
    """)
    refs = {r[0]: {"total": r[1], "completed": r[2]} for r in cur.fetchall()}
    conn.close()

    result = []
    for uid in set(members.keys()) | set(refs.keys()):
        m = members.get(uid, {})
        st = refs.get(uid, {})
        result.append({
            "user_id": uid,
            "username": m.get("username", "нет"),
            "full_name": m.get("full_name", f"ID {uid}"),
            "first_seen": m.get("first_seen", "—"),
            "last_seen": m.get("last_seen", "—"),
            "total": int(st.get("total", 0)),
            "completed": int(st.get("completed", 0))
        })
    result.sort(key=lambda x: x["total"], reverse=True)
    return jsonify({"staff": result})

@app.route("/api/admin/staff_detail")
def api_admin_staff_detail():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    sid = request.args.get("id")
    if not sid:
        return jsonify({"error": "no id"}), 400
    try:
        sid = int(sid)
    except:
        return jsonify({"error": "bad id"}), 400

    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT client_id, client_name, status, created_at
        FROM staff_referrals
        WHERE staff_id=?
        ORDER BY id DESC
        LIMIT 100
    """, (sid,))
    rows = cur.fetchall()
    conn.close()
    return jsonify({
        "items": [
            {
                "client_id": r[0],
                "client_name": r[1],
                "status": r[2],
                "created_at": r[3]
            } for r in rows
        ]
    })

@app.route("/api/admin/done")
def api_admin_done():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    cid = request.args.get("client_id")
    action = request.args.get("action", "done")
    if not cid:
        return jsonify({"error": "no client_id"}), 400
    try:
        cid = int(cid)
    except:
        return jsonify({"error": "bad client_id"}), 400

    status = "completed" if action == "done" else "started"
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("UPDATE staff_referrals SET status=? WHERE client_id=?", (status, cid))
    n = cur.rowcount
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "updated": n, "status": status})

@app.route("/api/admin/export")
def api_admin_export():
    if not check_key():
        return jsonify({"error": "forbidden"}), 403
    conn = sqlite3.connect("stats.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT staff_id, COUNT(*) FROM staff_referrals GROUP BY staff_id")
    staff = [{"staff_id": s, "total": c} for s, c in cur.fetchall()]
    conn.close()
    return jsonify({
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "users": users,
        "staff": staff
    })

# ===================== BOT UI =====================
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("💳 Карта Black"), types.KeyboardButton("💼 Бизнес-счёт"))
    kb.add(types.KeyboardButton("📈 Инвестиции"), types.KeyboardButton("🔍 Все продукты"))
    kb.add(types.KeyboardButton("✨ Почему выгодно"), types.KeyboardButton("⚠️ Важно"))
    return kb

def product_msg(title, points, btn_text, url):
    text = f"<b>{title}</b>\n\n" + "\n".join([f"• {p}" for p in points]) + "\n\n👇 Оформить в 1 клик"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(btn_text, url=url))
    return text, mk

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
    bot.send_message(
        message.chat.id,
        "✨ <b>Добро пожаловать в T-Bank бот</b>\n\n"
        "Здесь можно быстро оформить выгодные продукты банка онлайн.\n\n"
        "🔥 Бонусы • ⚡️ Быстро • 📱 Без визита в офис\n\n"
        "Выбери продукт ниже 👇",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: True)
def handle(message):
    if message.text and message.text.startswith("/"):
        return

    save_user(message.from_user)
    text = (message.text or "").lower()
    user_id = message.from_user.id

    if "black" in text or "карта" in text:
        add_click(user_id, "black")
        msg, mk = product_msg(
            "💳 T-Bank Black",
            ["Бонус 500 ₽", "Кэшбэк до 30%", "Часто 0 ₽ обслуживание", "Доставка карты"],
            "🚀 Оформить + 500 ₽", LINK_BLACK
        )
        bot.send_message(message.chat.id, msg, reply_markup=mk, parse_mode="HTML")

    elif "бизнес" in text:
        add_click(user_id, "business")
        msg, mk = product_msg(
            "💼 Бизнес-счёт",
            ["Открытие онлайн", "Для ИП и ООО", "Удобное приложение"],
            "💼 Открыть счёт", LINK_BUSINESS
        )
        bot.send_message(message.chat.id, msg, reply_markup=mk, parse_mode="HTML")

    elif "инвест" in text:
        add_click(user_id, "invest")
        msg, mk = product_msg(
            "📈 Инвестиции",
            ["Акции, облигации, ETF", "Старт с небольшой суммы", "Удобное приложение"],
            "📈 Открыть счёт", LINK_INVEST
        )
        bot.send_message(message.chat.id, msg, reply_markup=mk, parse_mode="HTML")

    elif "все продукт" in text or "выбери" in text:
        add_click(user_id, "all")
        msg, mk = product_msg(
            "🔍 Все продукты",
            ["Карты", "Бизнес", "Инвестиции", "Другие сервисы"],
            "🔍 Открыть каталог", LINK_ALL
        )
        bot.send_message(message.chat.id, msg, reply_markup=mk, parse_mode="HTML")

    elif "выгодно" in text:
        add_click(user_id, "why")
        bot.send_message(
            message.chat.id,
            "✨ <b>Почему это удобно</b>\n\n"
            "• Оформление онлайн\n• Бонусы\n• Быстрое решение\n• Всё в одном приложении",
            parse_mode="HTML"
        )

    elif "важно" in text:
        add_click(user_id, "important")
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Важно</b>\n\n"
            "1. Оформляй только по кнопке из бота\n"
            "2. Выполни условия акции\n"
            "3. Обычно нужна покупка или пополнение",
            parse_mode="HTML"
        )

    else:
        bot.send_message(message.chat.id, "Выбери продукт в меню 👇", reply_markup=main_keyboard())

def run_api():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_api, daemon=True).start()
    print("✅ Main bot + full admin API")
    bot.infinity_polling()
