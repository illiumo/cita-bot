import json
import os
from unittest.mock import call

from bot.utils.state_manager import user_states, file_path
from bot.handlers.subscription_handler import add_subscription_command
from bot.handlers.terms_handler import handle_terms
from bot.handlers.language_handler import get_translation, user_lang,language
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from bot.bot_instance import bot
from database.setup import SessionLocal
from database.models import User

def get_main_menu(user_id):
    lang = user_lang.get(user_id, "en")
    main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
    main_menu.add(KeyboardButton(get_translation(user_id, "select_language_menu")))
    main_menu.add(KeyboardButton(get_translation(user_id, "terms_menu")))
    main_menu.add(KeyboardButton(get_translation(user_id, "add_sub_menu")))
    main_menu.add(KeyboardButton(get_translation(user_id, "mng_sub_menu")))
    return main_menu


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    telegram_id = message.from_user.id
    bot.send_message(user_id, get_translation(user_id, "start"), reply_markup=get_main_menu(user_id))
    session = SessionLocal()
    try:
        # Проверяем, есть ли пользователь в базе
        user = session.query(User).filter_by(telegram_id=str(telegram_id)).first()
        if not user:
            # Создаем нового пользователя, если его нет
            user = User(telegram_id=str(telegram_id))
            session.add(user)
            session.commit()
    finally:
        session.close()


@bot.message_handler(func=lambda message: message.text in [
    get_translation(message.chat.id, "select_language_menu"),
    get_translation(message.chat.id, "terms_menu"),
    get_translation(message.chat.id, "add_sub_menu"),
    get_translation(message.chat.id, "mng_sub_menu"),
])
def handle_buttons(message):
    user_id = message.chat.id
    if message.text == get_translation(user_id, "select_language_menu"):
        language(message)
    elif message.text == get_translation(user_id, "terms_menu"):
        handle_terms(message)
    elif message.text == get_translation(user_id, "add_sub_menu"):
        add_subscription_command(message)
    elif message.text == get_translation(user_id, "mng_sub_menu"):
        bot.send_message(user_id, "This feature is not yet implemented.")