# -*- coding: utf-8 -*-
import datetime
import json
import os
import telebot
from telebot.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton)
from datetime import datetime, timedelta
from db_manager import add_subscription_sqlalchemy

translations = {
    "en": {
        "start": """Hi! 👋\nCita Previa Infobot is an instant notification service ⚡️ that alerts you when appointments become available on the Spanish immigration office’s website.\nHow does it work?\n1️⃣ Choose your region and the procedure (trámite) you need an appointment for (/add_subscription).\n2️⃣ Subscribe — payment can be made by card, Apple ID, or Google Play.\n3️⃣ We monitor the immigration website 24/7 throughout your subscription, saving you time and hassle.\n4️⃣ As soon as an appointment becomes available, we send you a notification in this chat.\n5️⃣ You follow the link and book your appointment yourself!\n🔥 Why choose us?\n✔️ Unlimited appointments — you can book for yourself and your whole family.\n✔️ Security — we don’t ask for personal data, our service complies with GDPR, and it’s suitable even for businesses.\n✔️ Flexibility — choose the city and time that suits you, and we’ll indicate available locations in the notifications.\n✔️ Ethical — we don’t resell appointments or interfere with the normal operation of the immigration office.\n✔️ Money-back guarantee — if you don’t receive any notifications during your subscription, we’ll refund your money!\n📌 Subscribe now and get notifications about available appointments hassle-free! 🚀""",
        "select_language": "Select your language:",
        "terms": """✅ We do not sell seats or support illegal markets.\n✅ Our service provides notifications about available slots, simplifying the booking process.\n✅ We do not collect your personal data except for minimal information passed through Telegram, necessary for proper service operation.\n✅ We guarantee service stability and provide a full refund if no notifications are sent within your subscription period.\n✅ We do not guarantee booking success as it depends on your actions. However, most users make a booking within a week.\n✅ The service is provided "as is" without additional guarantees, except in cases explicitly stated in these terms.""",
        "choose_province": "📍 Please select a province:",
        "next": "Next ➡️",
        "prev": "Back ⬅️",
        "select_language_menu": "Change language",
        "terms_menu": "Terms of service",
        "add_sub_menu": "Add subscription",
        "mng_sub_menu": "Manage my subscription",
    },
    "ru": {
        "start": """Привет! 👋\nCita Previa Infobot — это сервис мгновенных уведомлений ⚡️ о появлении доступных записей (сит) на портале иммиграционной службы Испании (сайт экстранхерии).\nКак это работает?\n1️⃣ Выбираете регион и процедуру (trámite), на которую нужна запись (/add_subscription).\n2️⃣ Оформляете подписку — оплата возможна картой, через Apple ID или Google Play.\n3️⃣ Мы мониторим сайт экстранхерии 24/7 на протяжении всего срока подписки, экономя ваше время и нервы.\n4️⃣ При появлении записи сразу отправляем вам уведомление в этот диалог.\n5️⃣ Вы переходите по ссылке и самостоятельно бронируете ситу!\n🔥 Почему стоит выбрать нас?\n✔️ Неограниченное количество записей — можно бронировать как для себя, так и для всей семьи.\n✔️ Безопасность — не запрашиваем личные данные, сервис соответствует GDPR и подходит даже для бизнеса.\n✔️ Гибкость — выбираете удобный город и время, в уведомлениях указываем доступные локации.\n✔️ Этичность — мы не перепродаем ситы и не мешаем нормальной работе иммиграционной службы.\n✔️ Гарантия возврата — если за весь срок подписки не придёт ни одного уведомления, вернём деньги!\n📌 Оформите подписку и получайте уведомления о появлении сит без лишних забот! 🚀""" ,
        "select_language": "Выберите язык:",
        "terms": """✅ Мы не продаем ситы и не поддерживаем нелегальный рынок записей.\n✅ Наш сервис предоставляет информационную услугу – уведомления о появлении свободных сит, что значительно упрощает процесс записи.\n✅ Мы не собираем ваши персональные данные за исключением минимальной информации, передаваемой Telegram, необходимой для корректной работы сервиса.\n✅ Мы гарантируем стабильность работы и полностью вернем деньги, если за весь срок подписки не отправим ни одного уведомления.\n✅ Мы не гарантируем успешное получение записи, так как это зависит от ваших действий. Однако большинство пользователей оформляют запись в течение недели.\n✅ Сервис предоставляется \"как есть\", без дополнительных гарантий, за исключением случаев, прямо указанных в данных условиях.""",
        "choose_province": "📍 Пожалуйста, выберите провинцию:",
        "next": "Далее ➡️",
        "prev": "Назад ⬅️",
        "select_language_menu": "Выбрать язык",
        "terms_menu": "Условия использования",
        "add_sub_menu": "Добавить подписку",
        "mng_sub_menu": "Управление подпиской",
    },
    "es": {
        "start": """¡Hola! 👋\nCita Previa Infobot es un servicio de notificaciones instantáneas ⚡️ sobre la disponibilidad de citas en el portal de la oficina de extranjería de España.\n¿Cómo funciona?\n1️⃣ Seleccionas la región y el trámite para el que necesitas una cita (/add_subscription).\n2️⃣ Suscríbete: el pago se puede realizar con tarjeta, Apple ID o Google Play.\n3️⃣ Monitoreamos el sitio web de extranjería 24/7 durante toda la suscripción, ahorrándote tiempo y preocupaciones.\n4️⃣ Cuando aparece una cita disponible, te enviamos una notificación en este chat.\n5️⃣ Sigues el enlace y reservas tu cita por tu cuenta.\n🔥 ¿Por qué elegirnos?\n✔️ Citas ilimitadas: puedes reservar para ti y para toda tu familia.\n✔️ Seguridad: no pedimos datos personales, el servicio cumple con el GDPR y es apto incluso para empresas.\n✔️ Flexibilidad: eliges la ciudad y el horario que prefieras, y te indicamos las ubicaciones disponibles.\n✔️ Ética: no revendemos citas ni interferimos con el funcionamiento normal de la oficina de extranjería.\n✔️ Garantía de reembolso: si durante tu suscripción no recibes ninguna notificación, te devolvemos el dinero.\n📌 ¡Suscríbete y recibe notificaciones sobre citas sin preocupaciones! 🚀""",
        "select_language": "Selecciona tu idioma:",
        "terms": """✅ No vendemos asientos ni apoyamos mercados ilegales.\n✅ Nuestro servicio proporciona notificaciones sobre espacios disponibles, simplificando el proceso de reserva.\n✅ No recopilamos sus datos personales, excepto la información mínima pasada por Telegram, necesaria para el funcionamiento correcto del servicio.\n✅ Garantizamos la estabilidad del servicio y brindamos un reembolso completo si no se envían notificaciones dentro de su período de suscripción.\n✅ No garantizamos el éxito de la reserva, ya que depende de sus acciones. Sin embargo, la mayoría de los usuarios hacen una reserva dentro de una semana.\n✅ El servicio se proporciona "tal cual" sin garantías adicionales, excepto en los casos que se indiquen explícitamente en estos términos.""",
        "choose_province": "📍 Por favor selecciona una provincia:",
        "next": "Siguiente ➡️",
        "prev": "Atrás ⬅️",
        "select_language_menu": "Cambiar idioma",
        "terms_menu": "Términos del servicio",
        "add_sub_menu": "Agregar suscripción",
        "mng_sub_menu": "Administrar suscripción",
    },
    "ua": {
        "start": """Привіт! 👋\nCita Previa Infobot — це сервіс миттєвих сповіщень ⚡️ про появу доступних записів (сит) на порталі імміграційної служби Іспанії (сайт екстранхерії).\nЯк це працює?\n1️⃣ Обираєте регіон і процедуру (trámite), на яку потрібен запис (/add_subscription).\n2️⃣ Оформлюєте підписку — оплата можлива карткою, через Apple ID або Google Play.\n3️⃣ Ми моніторимо сайт екстранхерії 24/7 протягом усього терміну підписки, заощаджуючи ваш час і нерви.\n4️⃣ Як тільки з’являється запис, ми одразу надсилаємо вам сповіщення у цей діалог.\n5️⃣ Ви переходите за посиланням і самостійно бронюєте ситу!\n🔥 Чому варто обрати нас?\n✔️ Необмежена кількість записів — можна бронювати як для себе, так і для всієї родини.\n✔️ Безпека — не запитуємо особисті дані, сервіс відповідає GDPR і підходить навіть для бізнесу.\n✔️ Гнучкість — обираєте зручне місто і час, у сповіщеннях вказуємо доступні локації.\n✔️ Етичність — ми не перепродаємо сити і не заважаємо нормальній роботі імміграційної служби.\n✔️ Гарантія повернення коштів — якщо протягом терміну підписки не надійде жодного сповіщення, повернемо гроші!\n📌 Оформіть підписку і отримуйте сповіщення про появу сит без зайвих турбот! 🚀""",
        "select_language": "Оберіть мову:",
        "terms": """✅ Ми не продаємо місця й не підтримуємо незаконний ринок записів.\n✅ Наш сервіс надає послугу повідомлення про доступні місця, що значно спрощує процес запису.\n✅ Ми не збираємо ваші персональні дані, за виключенням мінімальної інформації, яку передає Telegram, необхідної для коректної роботи сервісу.\n✅ Ми гарантуємо стабільність роботи й надаємо повне відшкодування, якщо протягом терміну підписки не буде надіслано жодного повідомлення.\n✅ Ми не гарантуємо успішного запису, оскільки це залежить від ваших дій. Однак більшість користувачів записуються протягом тижня.\n✅ Сервіс надається "як є" без додаткових гарантій, за винятком випадків, прямо зазначених у цих умовах.""",
        "choose_province": "📍 Будь ласка, оберіть провінцію:",
        "next": "Далі ➡️",
        "prev": "Назад ⬅️",
        "select_language_menu": "Змінити мову",
        "terms_menu": "Умови використання",
        "add_sub_menu": "Додати підписку",
        "mng_sub_menu": "Керування підпискою",
    },
}

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

user_states = {}

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


user_lang = load_user_lang()

TOKEN = "8029955410:AAELfmyIB8VriWQqfYimN4RCVzKSMHKsr9s"
bot = telebot.TeleBot(TOKEN)


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
    bot.send_message(user_id, get_translation(user_id, "start"), reply_markup=get_main_menu(user_id))


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

@bot.message_handler(commands=["language"])
def language(message):
    lang_menu = InlineKeyboardMarkup()
    lang_menu.add(InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"))
    lang_menu.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    lang_menu.add(InlineKeyboardButton("🇷🇺 Русский" , callback_data="lang_ru"))
    lang_menu.add(InlineKeyboardButton("🇺🇦 Українська" , callback_data="lang_ua"))
    bot.send_message(message.chat.id, get_translation(message.chat.id, "select_language"), reply_markup=lang_menu)

file_path = "/Utils/config.json"
PROVINCES_PER_PAGE = 8
PROCEDURES_PER_PAGE = 8



@bot.message_handler(commands=["terms"])
def handle_terms(message):
    user_id = message.chat.id
    bot.send_message(user_id, get_translation(user_id, "terms"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_next_"))
def next_page_callback(call):
    page = int(call.data.split("_")[-1])
    add_subscription_command(call.message, page=page, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    lang_code = call.data.split("_")[-1]
    user_lang[call.message.chat.id] = lang_code
    save_user_lang()
    bot.answer_callback_query(call.id, "Language updated!")
    bot.send_message(
        call.message.chat.id,
        get_translation(call.message.chat.id, "start"),
        reply_markup=get_main_menu(call.message.chat.id),
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
    finalize_subscription(call)


@bot.message_handler(commands=['add_subscription'])
def add_subscription_command(message):
    user_states[message.chat.id] = {}
    show_province_page(message.chat.id, 0)


def get_province_page(page=0):
    start = page * PROVINCES_PER_PAGE
    end = start + PROVINCES_PER_PAGE
    return all_provinces[start:end]

def get_procedures_by_province(province_name):
    """Получает список процедур по провинции из JSON файла"""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    province_data = data.get(province_name, {})

    # Собираем все процедуры в один список
    procedures = []
    for category in ["tramites_oficinas_extranjeria", "tramites_policia_nacional"]:
        if category in province_data:
            procedures.extend(province_data[category])  # Добавляем все процедуры

    return procedures  # Теперь это список, а не словарь



def get_procedures_page(province_name, page=0):
    """Возвращает часть процедур по указанной провинции для пагинации"""
    all_procedures = get_procedures_by_province(province_name)

    if not isinstance(all_procedures, list):
        print(f"❌ Ошибка! Ожидался список, но пришло: {type(all_procedures)} -> {all_procedures}")
        return []

    start = page * PROCEDURES_PER_PAGE
    end = start + PROCEDURES_PER_PAGE
    return all_procedures[start:end]



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


def show_procedures_page(chat_id, page, message_id=None):
    """Отображает список процедур по выбранной провинции и добавляет кнопки "Назад"."""
    province = user_states.get(chat_id, {}).get("province")
    if not province:
        bot.send_message(chat_id, "⚠️ Ошибка: провинция не выбрана. Попробуйте снова.")
        return

    procedures = get_procedures_page(province, page)

    if not procedures:
        bot.send_message(chat_id, f"❌ Нет доступных процедур для {province}.")
        return

    procedures_menu = InlineKeyboardMarkup(row_width=1)

    # Создаем кнопки для процедур
    buttons = [
        InlineKeyboardButton(proc["nombre"], callback_data=f"choose_procedure|{proc['valor']}")
        for proc in procedures if isinstance(proc, dict) and "nombre" in proc and "valor" in proc
    ]

    if not buttons:
        bot.send_message(chat_id, "⚠️ Ошибка: не удалось загрузить процедуры.")
        return

    procedures_menu.add(*buttons)

    # Добавляем кнопки "Назад" и "Назад к выбору провинции"
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"procedures_prev|{page - 1}"))
    if (page + 1) * PROCEDURES_PER_PAGE < len(get_procedures_by_province(province)):
        navigation_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"procedures_next|{page + 1}"))

    if navigation_buttons:
        procedures_menu.add(*navigation_buttons)

    procedures_menu.add(InlineKeyboardButton("🔙 Назад к выбору провинции", callback_data="back_to_provinces"))

    last_message_id = user_states.get(chat_id, {}).get("last_message_id")
    if last_message_id:
        try:
            bot.delete_message(chat_id, last_message_id)
        except:
            pass  # Если сообщение уже удалено, пропускаем

    sent_message = bot.send_message(chat_id, "📝 Выберите процедуру:", reply_markup=procedures_menu)
    user_states[chat_id]["last_message_id"] = sent_message.message_id

@bot.callback_query_handler(func=lambda call: call.data == "back_to_provinces")
def back_to_provinces(call):
    """Позволяет вернуться к выбору провинции"""
    chat_id = call.message.chat.id
    show_province_page(chat_id, 0)
    bot.delete_message(chat_id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("procedures_prev"))
def procedures_prev_page(call):
    """Обрабатывает нажатие кнопки 'Назад' для процедур"""
    chat_id = call.message.chat.id
    page = int(call.data.split("|")[-1])
    show_procedures_page(chat_id, page)

@bot.callback_query_handler(func=lambda call: call.data.startswith("procedures_next"))
def procedures_next_page(call):
    """Обрабатывает нажатие кнопки 'Далее' для процедур"""
    chat_id = call.message.chat.id
    page = int(call.data.split("|")[-1])
    show_procedures_page(chat_id, page)

@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_province"))
def choose_province(call):
    """Обрабатывает выбор провинции и предлагает выбрать процедуру"""
    _, province = call.data.split("|")
    chat_id = call.message.chat.id
    user_states[chat_id] = {'province': province}  # Сохраняем провинцию в user_states
    bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(chat_id, f"📌 Вы выбрали провинцию: {province}")
    show_procedures_page(chat_id, 0)

def get_procedure(message):
    """Пользователь вводит процедуру."""
    chat_id = message.chat.id
    procedure = message.text.strip()
    user_states[chat_id]['procedure'] = procedure

    bot.send_message(chat_id, f"📝 Процедура: {procedure}")
    ask_all_addresses(chat_id)

###############################################################################
# Выбор адресов: все или конкретные
###############################################################################
def ask_all_addresses(chat_id):
    """Предлагаем пользователю выбрать: все адреса или ввести конкретные."""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📍 Все адреса", callback_data="addresses_all"),
        InlineKeyboardButton("🏢 Указать адреса", callback_data="addresses_custom")
    )
    bot.send_message(chat_id, "Выберите вариант подписки:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "addresses_all")
def addresses_all_handler(call):
    """Пользователь выбрал все адреса."""
    chat_id = call.message.chat.id
    if chat_id not in user_states:
        bot.send_message(chat_id, "⚠️ Сначала введите /add_subscription.")
        return

    user_states[chat_id]['addresses'] = ['ALL']
    select_subscription_plan(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "addresses_custom")
def addresses_custom_handler(call):
    """Пользователь хочет ввести адреса вручную."""
    chat_id = call.message.chat.id
    if chat_id not in user_states:
        bot.send_message(chat_id, "⚠️ Сначала введите /add_subscription.")
        return

    bot.send_message(chat_id, "🏢 Введите список адресов (через запятую):")
    bot.register_next_step_handler(call.message, save_addresses)

def save_addresses(message):
    """Пользователь вводит адрес(а) в тексте."""
    chat_id = message.chat.id
    if chat_id not in user_states:
        bot.send_message(chat_id, "⚠️ Сначала введите /add_subscription.")
        return

    addresses = [addr.strip() for addr in message.text.split(",") if addr.strip()]
    user_states[chat_id]['addresses'] = addresses
    select_subscription_plan(message)

###############################################################################
# Выбор тарифа
###############################################################################
def select_subscription_plan(message):
    """Показываем кнопки: 7 дней, 14 дней, 30 дней."""
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⭐ 750 на 7 дней", callback_data="sub_7"),
        InlineKeyboardButton("👍 1500 на 14 дней", callback_data="sub_14"),
        InlineKeyboardButton("📅 2500 на 30 дней", callback_data="sub_30")
    )
    bot.send_message(chat_id, "Выберите ваш вариант подписки:", reply_markup=markup)

###############################################################################
# Завершение подписки
###############################################################################
@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def finalize_subscription(call):
    """Пользователь выбрал срок подписки (7, 14, 30 дней)."""
    chat_id = call.message.chat.id
    try:
        # Из call.data типа "sub_7" выделяем "7"
        days_str = call.data.split("_")[1]
        days = int(days_str)

        # Получаем данные из user_states
        data = user_states.get(chat_id, {})
        if not data:
            bot.send_message(chat_id, "⚠️ Ошибка: данные подписки не найдены. Попробуйте снова (/add_subscription).")
            return

        # Пример даты истечения (пока строка, если нужно, храним как datetime)
        expiration_date = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        # Вызываем вашу функцию добавления в БД
        # (Эту функцию напишите сами: add_subscription_sqlalchemy, например)
        # Или если вам нужно expiration_date, добавьте параметр туда тоже
        added_sub = add_subscription_sqlalchemy(
            user_id=chat_id,
            telegram_handle=f"@{call.from_user.username}" if call.from_user.username else "",
            phone_number="",
            service_name=f"{days} дневная подписка",
            province=data.get('province', 'Не указано'),
            procedure=data.get('procedure', 'Не указано'),
            addresses=data.get('addresses', ['ALL']),
            subscription_days=days,
        )

        # Сообщаем пользователю результат
        bot.send_message(
            chat_id,
            "✅ *Подписка оформлена!* 🎉\n\n"
            f"📌 *Процедура:* {data.get('procedure', 'Не указано')}\n"
            f"📍 *Провинция:* {data.get('province', 'Не указано')}\n"
            f"🏢 *Отделение:* {', '.join(data.get('addresses', ['ALL']))}\n"
            f"📅 *Подписка действует до:* {expiration_date}\n\n"
            "_Спасибо за использование нашего сервиса!_",
            parse_mode="Markdown"
        )
        # Удаляем состояние
        user_states.pop(chat_id, None)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")


if __name__ == "__main__":
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)
