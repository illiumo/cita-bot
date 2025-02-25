from bot.bot_instance import bot
from bot.handlers.start_handler import *
from bot.handlers.subscription_handler import *
from bot.handlers.language_handler import *
from bot.handlers.terms_handler import *
print("🤖 Бот запущен...")
bot.polling(none_stop=True)