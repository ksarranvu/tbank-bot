import os
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

# ================= ССЫЛКИ =================
LINK_BLACK = "https://tbank.ru/baf/6cDotN3sm66"
LINK_BUSINESS = "https://tbank.ru/baf/4fWsjkGRCpn"
LINK_INVEST = "https://tbank.ru/baf/4Nha2vM22nm"
LINK_ALL = "https://tbank.ru/baf/58KGejb8KDQ"

# Картинка из GitHub (raw)
PHOTO_URL = "https://raw.githubusercontent.com/ksarranvu/tbank-bot/main/welcome.png"

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("💳 Карта Black + 500 ₽"))
    markup.add(types.KeyboardButton("💼 Бизнес-счёт"))
    markup.add(types.KeyboardButton("📈 Счёт для инвестиций"))
    markup.add(types.KeyboardButton("🔍 Выбери продукт сам"))
    markup.add(types.KeyboardButton("📋 Подробнее о продуктах"))
    markup.add(types.KeyboardButton("🔥 Почему это выгодно"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Здесь можно быстро оформить выгодные продукты Т-Банка.\n\n"
        "Выбирай, что тебе интересно 👇"
    )
    try:
        bot.send_photo(
            message.chat.id,
            PHOTO_URL,
            caption=text,
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    except:
        # Если картинка не загрузится — просто текст
        bot.send_message(message.chat.id, text, reply_markup=main_keyboard(), parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle(message):
    text = message.text.lower()

    if "карта" in text or "black" in text or "500" in text:
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
        desc = (
            "🔍 <b>Выбери продукт сам</b>\n\n"
            "На странице доступны все продукты Т-Банка:\n"
            "карты, бизнес-счёт, инвестиции и другое."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔍 Выбрать продукт", url=LINK_ALL))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    elif "подробнее" in text:
        text_info = (
            "📋 <b>Кратко о продуктах:</b>\n\n"
            "💳 Карта Black — кэшбэк + 500 ₽\n"
            "💼 Бизнес-счёт — для ИП и ООО\n"
            "📈 Инвестиции — акции и облигации\n"
            "🔍 Выбери сам — все продукты банка"
        )
        bot.send_message(message.chat.id, text_info, parse_mode="HTML")

    elif "выгодно" in text:
        bot.send_message(message.chat.id, "🔥 Всё оформляется онлайн, часто есть бонусы и удобные приложения.")

    else:
        bot.send_message(message.chat.id, "Используй кнопки меню 👇", reply_markup=main_keyboard())

print("✅ Бот запущен!")
bot.infinity_polling()
