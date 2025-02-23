import telebot
from telebot.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton)

# Токен бота
TOKEN = "TOKEN"
bot = telebot.TeleBot(TOKEN)

# Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("/start", "/language", "/terms")
main_menu.add("/add_subscription")
main_menu.add("/my_subscriptions", "/manage_subscriptions")

# Список всех провинций
all_provinces = [
    "A Coruña", "Albacete", "Alicante", "Almería", "Araba", "Asturias", "Ávila", "Badajoz",
    "Barcelona", "Bizkaia", "Burgos", "Cáceres", "Cádiz", "Cantabria", "Castellón", "Ceuta",
    "Ciudad Real", "Córdoba", "Cuenca", "Gipuzkoa", "Girona", "Granada", "Guadalajara", "Huelva",
    "Huesca", "Illes Balears", "Jaén", "La Rioja", "Las Palmas", "León", "Lleida", "Lugo",
    "Madrid", "Málaga", "Melilla", "Murcia", "Navarra", "Ourense", "Palencia", "Pontevedra",
    "Salamanca", "S.Cruz Tenerife", "Segovia", "Sevilla", "Soria", "Tarragona", "Teruel", "Toledo",
    "Valencia", "Valladolid", "Zamora", "Zaragoza"
]

@bot.message_handler(commands=['language'])
def language(message):
    lang_menu = InlineKeyboardMarkup()
    lang_menu.add(InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"))
    lang_menu.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    lang_menu.add(InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    lang_menu.add(InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"))
    bot.send_message(message.chat.id, "Выберите язык:", reply_markup=lang_menu)


# Разбиение списка провинций на страницы
PROVINCES_PER_PAGE = 8


def get_province_page(page=0):
    start = page * PROVINCES_PER_PAGE
    end = start + PROVINCES_PER_PAGE
    return all_provinces[start:end]

@bot.message_handler(commands=["terms"])
def handle_terms(message):
    lang_menu = InlineKeyboardMarkup()
    bot.send_message(message.chat.id, '✅ Мы не продаем ситы и не поддерживаем нелегальный рынок записей. Вы бронируете их самостоятельно.\n✅ Наш сервис предоставляет информационную услугу – уведомления о появлении свободных сит, что значительно упрощает процесс записи.\n✅ Мы не собираем ваши персональные данные за исключением минимальной информации, передаваемой Telegram, необходимой для корректной работы сервиса.\n✅ Мы гарантируем стабильность работы и полностью вернем деньги, если за весь срок подписки не отправим ни одного уведомления.\n✅ Мы не гарантируем успешное получение записи, так как это зависит от ваших действий. Однако большинство пользователей оформляют запись в течение недели.\n✅ Сервис предоставляется "как есть", без дополнительных гарантий, за исключением случаев, прямо указанных в данных условиях.',reply_markup=lang_menu)
@bot.message_handler(commands=['add_subscription'])
def add_subscription(message, page=0, message_id=None):
    provinces_menu = InlineKeyboardMarkup(row_width=2)
    provinces = get_province_page(page)
    buttons = [InlineKeyboardButton(province, callback_data=f"sub_{province}") for province in provinces]
    provinces_menu.add(*buttons)

    if (page + 1) * PROVINCES_PER_PAGE < len(all_provinces):
        provinces_menu.add(InlineKeyboardButton("Далее ➡️", callback_data=f"sub_next_{page + 1}"))

    if message_id:
        bot.edit_message_reply_markup(message.chat.id, message_id, reply_markup=provinces_menu)
    else:
        sent_message = bot.send_message(message.chat.id, "📍 Пожалуйста, выберите провинцию:",
                                        reply_markup=provinces_menu)
        bot.register_next_step_handler(sent_message, add_subscription, page=page, message_id=sent_message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_next_"))
def next_page_callback(call):
    page = int(call.data.split("_")[-1])
    add_subscription(call.message, page=page, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)


if __name__ == "__main__":
    bot.polling(none_stop=True)
