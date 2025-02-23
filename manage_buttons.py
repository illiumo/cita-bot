# -*- coding: utf-8 -*-
import json
import os
import telebot
from telebot.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton)
from db_manager import add_subscription

# A dictionary with all the languages listed
translations = {
    "en": {
        "start": """✅ We do not sell seats or support illegal markets.\n✅ Our service provides notifications about available slots, simplifying the booking process.\n✅ We do not collect your personal data except for minimal information passed through Telegram, necessary for proper service operation.\n✅ We guarantee service stability and provide a full refund if no notifications are sent within your subscription period.\n✅ We do not guarantee booking success as it depends on your actions. However, most users make a booking within a week.\n✅ The service is provided "as is" without additional guarantees, except in cases explicitly stated in these terms.\n✅ To switch the bot language, use the /language command.""",
        "select_language": "Select your language:",
        "terms": """✅ We do not sell seats or support illegal markets.\n✅ Our service provides notifications about available slots, simplifying the booking process.\n✅ We do not collect your personal data except for minimal information passed through Telegram, necessary for proper service operation.\n✅ We guarantee service stability and provide a full refund if no notifications are sent within your subscription period.\n✅ We do not guarantee booking success as it depends on your actions. However, most users make a booking within a week.\n✅ The service is provided "as is" without additional guarantees, except in cases explicitly stated in these terms.""",
        "choose_province": "📍 Please select a province:",
        "next": "Next ➡️",
    },
    "ru": {
        "start": """✅ Мы не продаем ситы и не поддерживаем нелегальный рынок записей.\n✅ Наш сервис предоставляет информационную услугу – уведомления о появлении свободных сит, что значительно упрощает процесс записи.\n✅ Мы не собираем ваши персональные данные за исключением минимальной информации, передаваемой Telegram, необходимой для корректной работы сервиса.\n✅ Мы гарантируем стабильность работы и полностью вернем деньги, если за весь срок подписки не отправим ни одного уведомления.\n✅ Мы не гарантируем успешное получение записи, так как это зависит от ваших действий. Однако большинство пользователей оформляют запись в течение недели.\n✅ Сервис предоставляется \"как есть\", без дополнительных гарантий, за исключением случаев, прямо указанных в данных условиях.\n✅ Чтобы изменить язык бота, используйте команду /language.""",
        "select_language": "Выберите язык:",
        "terms": """✅ Мы не продаем ситы и не поддерживаем нелегальный рынок записей.\n✅ Наш сервис предоставляет информационную услугу – уведомления о появлении свободных сит, что значительно упрощает процесс записи.\n✅ Мы не собираем ваши персональные данные за исключением минимальной информации, передаваемой Telegram, необходимой для корректной работы сервиса.\n✅ Мы гарантируем стабильность работы и полностью вернем деньги, если за весь срок подписки не отправим ни одного уведомления.\n✅ Мы не гарантируем успешное получение записи, так как это зависит от ваших действий. Однако большинство пользователей оформляют запись в течение недели.\n✅ Сервис предоставляется \"как есть\", без дополнительных гарантий, за исключением случаев, прямо указанных в данных условиях.""",
        "choose_province": "📍 Пожалуйста, выберите провинцию:",
        "next": "Далее ➡️",
    },
    "es": {
        "start": """✅ No vendemos asientos ni apoyamos mercados ilegales.\n✅ Nuestro servicio proporciona notificaciones sobre espacios disponibles, simplificando el proceso de reserva.\n✅ No recopilamos sus datos personales, excepto la información mínima pasada por Telegram, necesaria para el funcionamiento correcto del servicio.\n✅ Garantizamos la estabilidad del servicio y brindamos un reembolso completo si no se envían notificaciones dentro de su período de suscripción.\n✅ No garantizamos el éxito de la reserva, ya que depende de sus acciones. Sin embargo, la mayoría de los usuarios hacen una reserva dentro de una semana.\n✅ El servicio se proporciona "tal cual" sin garantías adicionales, excepto en los casos que se indiquen explícitamente en estos términos.\n✅ Para cambiar el idioma del bot, use el comando /language.""",
        "select_language": "Selecciona tu idioma:",
        "terms": """✅ No vendemos asientos ni apoyamos mercados ilegales.\n✅ Nuestro servicio proporciona notificaciones sobre espacios disponibles, simplificando el proceso de reserva.\n✅ No recopilamos sus datos personales, excepto la información mínima pasada por Telegram, necesaria para el funcionamiento correcto del servicio.\n✅ Garantizamos la estabilidad del servicio y brindamos un reembolso completo si no se envían notificaciones dentro de su período de suscripción.\n✅ No garantizamos el éxito de la reserva, ya que depende de sus acciones. Sin embargo, la mayoría de los usuarios hacen una reserva dentro de una semana.\n✅ El servicio se proporciona "tal cual" sin garantías adicionales, excepto en los casos que se indiquen explícitamente en estos términos.""",
        "choose_province": "📍 Por favor selecciona una provincia:",
        "next": "Siguiente ➡️",
    },
    "ua": {
        "start": """✅ Ми не продаємо місця й не підтримуємо незаконний ринок записів.\n✅ Наш сервіс надає послугу повідомлення про доступні місця, що значно спрощує процес запису.\n✅ Ми не збираємо ваші персональні дані, за виключенням мінімальної інформації, яку передає Telegram, необхідної для коректної роботи сервісу.\n✅ Ми гарантуємо стабільність роботи й надаємо повне відшкодування, якщо протягом терміну підписки не буде надіслано жодного повідомлення.\n✅ Ми не гарантуємо успішного запису, оскільки це залежить від ваших дій. Однак більшість користувачів записуються протягом тижня.\n✅ Сервіс надається "як є" без додаткових гарантій, за винятком випадків, прямо зазначених у цих умовах.\n✅ Щоб змінити мову бота, скористайтеся командою /language.""",
        "select_language": "Оберіть мову:",
        "terms": """✅ Ми не продаємо місця й не підтримуємо незаконний ринок записів.\n✅ Наш сервіс надає послугу повідомлення про доступні місця, що значно спрощує процес запису.\n✅ Ми не збираємо ваші персональні дані, за виключенням мінімальної інформації, яку передає Telegram, необхідної для коректної роботи сервісу.\n✅ Ми гарантуємо стабільність роботи й надаємо повне відшкодування, якщо протягом терміну підписки не буде надіслано жодного повідомлення.\n✅ Ми не гарантуємо успішного запису, оскільки це залежить від ваших дій. Однак більшість користувачів записуються протягом тижня.\n✅ Сервіс надається "як є" без додаткових гарантій, за винятком випадків, прямо зазначених у цих умовах.""",
        "choose_province": "📍 Будь ласка, оберіть провінцію:",
        "next": "Далі ➡️",
    },
}

language_file = "user_lang.json"
if not os.path.exists(language_file):
    with open(language_file, "w") as f:
        json.dump({}, f)


def load_user_lang():
    with open(language_file, "r") as f:
        return json.load(f)

def save_user_lang():
    with open(language_file, "w") as f:
        json.dump(user_lang, f)

user_lang = load_user_lang();

# Токен бота
TOKEN = "8029955410:AAELfmyIB8VriWQqfYimN4RCVzKSMHKsr9s"
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


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    bot.send_message(user_id, get_translation(user_id, "start"), reply_markup=main_menu)

@bot.message_handler(commands=["language"])
def language(message):
    lang_menu = InlineKeyboardMarkup()
    lang_menu.add(InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"))
    lang_menu.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    lang_menu.add(InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    lang_menu.add(InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"))
    bot.send_message(message.chat.id, get_translation(message.chat.id, "select_language"), reply_markup=lang_menu)


# Разбиение списка провинций на страницы
PROVINCES_PER_PAGE = 8
user_states = {}

def get_province_page(page=0):
    start = page * PROVINCES_PER_PAGE
    end = start + PROVINCES_PER_PAGE
    return all_provinces[start:end]

@bot.message_handler(commands=["terms"])
def handle_terms(message):
    user_id = message.chat.id
    bot.send_message(user_id, get_translation(user_id, "terms"))

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

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    lang_code = call.data.split("_")[-1]
    user_lang[call.message.chat.id] = lang_code
    save_user_lang()
    bot.send_message(call.id, "Language updated!")
    bot.send_message(
        call.message.chat.id,
        get_translation(call.message.chat.id, "start"),
        reply_markup=main_menu,
    )


def get_translation(user_id, k):
    lang = user_lang.get(user_id, "en")
    return translations.get(lang, {}).get(k, "Translation not found!")


def ask_all_addresses(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Все адреса", callback_data="addresses_all"),
        InlineKeyboardButton("Указать адреса", callback_data="addresses_custom")
    )
    bot.send_message(chat_id, "Хотите подписаться на все адреса или выбрать конкретные?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "addresses_all")
def addresses_all_handler(call):
    user_states[call.message.chat.id]['addresses'] = ['ALL']
    finalize_subscription(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "addresses_custom")
def addresses_custom_handler(call):
    bot.send_message(call.message.chat.id, "Введите список адресов (через запятую): ")
    bot.register_next_step_handler(call.message, save_addresses)


def save_addresses(message):
    addresses = [addr.strip() for addr in message.text.split(",") if addr.strip()]
    user_states[message.chat.id]['addresses'] = addresses
    finalize_subscription(message)


def finalize_subscription(message):
    chat_id = message.chat.id
    data = user_states[chat_id]
    province = data['province']
    procedure = data['procedure']
    addresses = data['addresses']

    service_name = "7 дневная подписка"
    phone_number = ""
    user_id = chat_id
    telegram_handle = f"@{message.from_user.username}" if message.from_user.username else ""

    added_sub = add_subscription(user_id, telegram_handle, phone_number, service_name, province, procedure, addresses,
                                 7)

    bot.send_message(chat_id, f"✅ Подписка оформлена!\n\n{added_sub}", reply_markup=main_menu)
    user_states.pop(chat_id, None)


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)




if __name__ == "__main__":
    bot.polling(none_stop=True)
