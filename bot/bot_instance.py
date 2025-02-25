import json
import os
import telebot
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "/Users/dragonav/PycharmProjects/cita-bot/bot/Utils/BOT_TOKEN.json")
with open(TOKEN_PATH, "r", encoding="utf-8") as file:
    bot_token_data = json.load(file)

BOT_TOKEN = bot_token_data["BOT_TOKEN"]
bot = telebot.TeleBot(BOT_TOKEN)
