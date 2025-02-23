import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from db_manager import add_subscription

TOKEN = "8029955410:AAELfmyIB8VriWQqfYimN4RCVzKSMHKsr9s"
bot = telebot.TeleBot(TOKEN)

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("📌 Добавить подписку", "📋 Мои подписки")
main_menu.add("⚙️ Управление подписками", "ℹ️ Условия использования")

all_provinces = [
    "A Coruña", "Albacete", "Alicante", "Almería", "Araba", "Asturias", "Ávila", "Badajoz",
    "Barcelona", "Bizkaia", "Burgos", "Cáceres", "Cádiz", "Cantabria", "Castellón", "Ceuta",
    "Ciudad Real", "Córdoba", "Cuenca", "Gipuzkoa", "Girona", "Granada", "Guadalajara", "Huelva",
    "Huesca", "Illes Balears", "Jaén", "La Rioja", "Las Palmas", "León", "Lleida", "Lugo",
    "Madrid", "Málaga", "Melilla", "Murcia", "Navarra", "Ourense", "Palencia", "Pontevedra",
    "Salamanca", "S.Cruz Tenerife", "Segovia", "Sevilla", "Soria", "Tarragona", "Teruel", "Toledo",
    "Valencia", "Valladolid", "Zamora", "Zaragoza"
]

PROVINCES_PER_PAGE = 8
user_states = {}


def get_province_page(page=0):
    start = page * PROVINCES_PER_PAGE
    end = start + PROVINCES_PER_PAGE
    return all_provinces[start:end]


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "👋 Привет! Этот бот поможет вам получать уведомления о свободных ситах.",
                     reply_markup=main_menu)


@bot.message_handler(commands=["terms"])
def handle_terms(message):
    bot.send_message(
        message.chat.id,
        "✅ Мы не продаем ситы и не поддерживаем нелегальный рынок записей.\n"
        "✅ Наш сервис предоставляет только уведомления о свободных ситах.\n"
        "✅ Мы не собираем персональные данные, кроме тех, что передаёт Telegram.\n",
        reply_markup=ReplyKeyboardRemove()
    )


@bot.message_handler(commands=['add_subscription'])
def add_subscription_command(message):
    user_states[message.chat.id] = {}
    show_province_page(message.chat.id, 0)


def show_province_page(chat_id, page):
    provinces_menu = InlineKeyboardMarkup(row_width=2)
    provinces = get_province_page(page)
    buttons = [
        InlineKeyboardButton(province, callback_data=f"choose_province|{province}")
        for province in provinces
    ]
    provinces_menu.add(*buttons)

    if (page + 1) * PROVINCES_PER_PAGE < len(all_provinces):
        provinces_menu.add(
            InlineKeyboardButton("➡️ Далее", callback_data=f"province_next|{page + 1}")
        )

    bot.send_message(chat_id, "📍 Выберите провинцию:", reply_markup=provinces_menu)


@bot.callback_query_handler(func=lambda call: call.data.startswith("province_next"))
def province_next_page(call):
    _, page_str = call.data.split("|")
    page = int(page_str)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    show_province_page(call.message.chat.id, page)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_province"))
def choose_province(call):
    _, province = call.data.split("|")
    user_states[call.message.chat.id]['province'] = province
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, f"📌 Вы выбрали провинцию: {province}")
    bot.send_message(call.message.chat.id, "✍️ Введите процедуру (например, 'Toma de huellas'):")
    bot.register_next_step_handler(call.message, get_procedure)


def get_procedure(message):
    procedure = message.text.strip()
    user_states[message.chat.id]['procedure'] = procedure
    bot.send_message(message.chat.id, f"📝 Процедура: {procedure}")
    ask_all_addresses(message.chat.id)


def ask_all_addresses(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📍 Все адреса", callback_data="addresses_all"),
        InlineKeyboardButton("🏢 Указать адреса", callback_data="addresses_custom")
    )
    bot.send_message(chat_id, "Выберите вариант подписки:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "addresses_all")
def addresses_all_handler(call):
    user_states[call.message.chat.id]['addresses'] = ['ALL']
    finalize_subscription(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "addresses_custom")
def addresses_custom_handler(call):
    bot.send_message(call.message.chat.id, "🏢 Введите список адресов (через запятую):")
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

    service_name = "7 дневная подписка" # чекни в боте как сделать там красиво все
    phone_number = ""
    user_id = chat_id
    telegram_handle = f"@{message.from_user.username}" if message.from_user.username else ""

    added_sub = add_subscription(user_id, telegram_handle, phone_number, service_name, province, procedure, addresses,
                                 7)

    bot.send_message(chat_id,
                     f"✅ *Подписка оформлена!*\n\n📌 *Процедура:* {procedure}\n📍 *Провинция:* {province}\n🏢 *Отделение:* {', '.join(addresses)}\n\n_Спасибо за использование нашего сервиса!_",
                     parse_mode="Markdown", reply_markup=main_menu)
    user_states.pop(chat_id, None)


if __name__ == "__main__":
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)
