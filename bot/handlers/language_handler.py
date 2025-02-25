import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.bot_instance import bot

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

def get_translation(user_id, k):
    lang = user_lang.get(user_id, "en")
    return translations.get(lang, {}).get(k, "Translation not found!")


@bot.message_handler(commands=["language"])
def language(message):
    lang_menu = InlineKeyboardMarkup()
    lang_menu.add(InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"))
    lang_menu.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    lang_menu.add(InlineKeyboardButton("🇷🇺 Русский" , callback_data="lang_ru"))
    lang_menu.add(InlineKeyboardButton("🇺🇦 Українська" , callback_data="lang_ua"))
    bot.send_message(message.chat.id, get_translation(message.chat.id, "select_language"), reply_markup=lang_menu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    from bot.handlers.start_handler import get_main_menu
    lang_code = call.data.split("_")[-1]
    user_lang[call.message.chat.id] = lang_code
    save_user_lang()
    bot.answer_callback_query(call.id, "Language updated!")
    bot.send_message(
        call.message.chat.id,
        get_translation(call.message.chat.id, "start"),

        reply_markup=get_main_menu(call.message.chat.id),
    )
