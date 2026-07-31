@bot.message_handler(content_types=['photo'])
def get_file_id(message):
    file_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, f"file_id:\n`{file_id}`", parse_mode="Markdown")
