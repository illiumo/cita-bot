from bot.bot_instance import bot
from bot.handlers.language_handler import *

@bot.message_handler(commands=["terms"])
def handle_terms(message):
    user_id = message.chat.id
    bot.send_message(user_id, get_translation(user_id, "terms"))