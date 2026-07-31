import os
import telebot

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

@bot.message_handler(content_types=['photo'])
def get_id(message):
    file_id = message.photo[-1].file_id
    bot.reply_to(message, f"Вот file_id:\n\n`{file_id}`", parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Пришли мне картинку")

print("Бот запущен")
bot.infinity_polling()
