import telebot
from telebot import types

TOKEN = "8710832670:AAEjPvRO0_ETb5pXCjRDFPw5SeGgbbU-fYg"

bot = telebot.TeleBot(TOKEN)

# ================= ССЫЛКИ =================
LINK_BLACK = "https://tbank.ru/baf/6cDotN3sm66"
LINK_BUSINESS = "https://tbank.ru/baf/4fWsjkGRCpn"
LINK_INVEST = "https://tbank.ru/baf/4Nha2vM22nm"
LINK_ALL = "https://tbank.ru/baf/58KGejb8KDQ"

# ================= ГЛАВНОЕ МЕНЮ =================
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
    text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Здесь можно быстро оформить выгодные продукты Т-Банка.\n\n"
        "Выбирай, что тебе интересно 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard(), parse_mode="HTML")

# ================= ОБРАБОТКА ВСЕХ КНОПОК =================
@bot.message_handler(func=lambda message: True)
def handle(message):
    text = message.text.lower()

    # ——— Карта Black ———
    if "карта" in text or "black" in text or "500" in text:
        desc = (
            "💳 <b>Дебетовая карта T-Bank Black</b>\n\n"
            "• Кэшбэк до 30% у партнёров\n"
            "• До 15% в 4 выбранных категориях\n"
            "• 500 ₽ в подарок при оформлении\n"
            "• Часто бесплатное обслуживание\n"
            "• Бесплатные переводы и пополнение\n"
            "• Работает за границей\n"
            "• Удобное приложение и поддержка 24/7\n\n"
            "Оформление онлайн, карта приедет домой."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 Оформить карту + 500 ₽", url=LINK_BLACK))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    # ——— Бизнес-счёт ———
    elif "бизнес" in text:
        desc = (
            "💼 <b>Бизнес-счёт Т-Банка</b>\n\n"
            "• Открытие за несколько минут онлайн\n"
            "• Удобное приложение для бизнеса\n"
            "• Бесплатные переводы и платежи\n"
            "• Интеграция с 1С, МойСклад и другими сервисами\n"
            "• Выгодные тарифы для ИП и ООО\n"
            "• Поддержка бизнеса 24/7\n"
            "• Возможность получать зарплату себе и сотрудникам\n\n"
            "Идеально подходит для предпринимателей."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💼 Открыть бизнес-счёт", url=LINK_BUSINESS))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    # ——— Инвестиции ———
    elif "инвест" in text:
        desc = (
            "📈 <b>Счёт для инвестиций (Т-Инвестиции)</b>\n\n"
            "• Открытие брокерского счёта онлайн\n"
            "• Акции, облигации, ETF, валюта и многое другое\n"
            "• Низкие комиссии\n"
            "• Удобное приложение с аналитикой\n"
            "• Можно начать с небольшой суммы\n"
            "• Обучение и подсказки для новичков\n"
            "• Возможность получать дивиденды и купоны\n\n"
            "Хороший способ начать инвестировать."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📈 Открыть инвестиционный счёт", url=LINK_INVEST))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    # ——— Выбери продукт сам ———
    elif "выбери" in text or "продукт сам" in text:
        desc = (
            "🔍 <b>Выбери продукт сам</b>\n\n"
            "На этой странице ты можешь самостоятельно посмотреть все доступные продукты Т-Банка:\n\n"
            "• Дебетовые и кредитные карты\n"
            "• Бизнес-счёт\n"
            "• Инвестиции\n"
            "• Кредиты и другие услуги\n\n"
            "Выбирай то, что тебе подходит больше всего."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔍 Выбрать продукт", url=LINK_ALL))
        bot.send_message(message.chat.id, desc, reply_markup=markup, parse_mode="HTML")

    # ——— Подробнее о продуктах ———
    elif "подробнее" in text:
        text_info = (
            "📋 <b>Кратко о всех продуктах:</b>\n\n"
            "💳 <b>Карта Black</b>\n"
            "Кэшбэк до 30%, 500 ₽ в подарок, удобное приложение.\n\n"
            "💼 <b>Бизнес-счёт</b>\n"
            "Для ИП и ООО. Быстрое открытие, удобные платежи, интеграция с сервисами.\n\n"
            "📈 <b>Инвестиционный счёт</b>\n"
            "Акции, облигации, ETF. Можно начать с небольшой суммы.\n\n"
            "🔍 <b>Выбери сам</b>\n"
            "Полный список всех продуктов банка на одной странице.\n\n"
            "Нажми на нужную кнопку в меню, чтобы перейти к оформлению."
        )
        bot.send_message(message.chat.id, text_info, parse_mode="HTML")

    # ——— Почему выгодно ———
    elif "выгодно" in text:
        text_why = (
            "🔥 <b>Почему это действительно выгодно:</b>\n\n"
            "• Все продукты оформляются полностью онлайн\n"
            "• Нет необходимости идти в отделение\n"
            "• Часто есть бонусы при оформлении\n"
            "• Удобные приложения и хорошая поддержка\n"
            "• Выгодные условия по кэшбэку, переводам и тарифам\n"
            "• Можно выбрать именно то, что нужно именно тебе\n\n"
            "Многие уже пользуются этими продуктами и остаются довольны."
        )
        bot.send_message(message.chat.id, text_why, parse_mode="HTML")

    else:
        bot.send_message(message.chat.id, "Пожалуйста, используй кнопки меню 👇", reply_markup=main_keyboard())

print("✅ Бот успешно запущен!")
bot.infinity_polling()