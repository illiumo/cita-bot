import json
import datetime
from datetime import timedelta
import re
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from database.setup import SessionLocal
from database.models import User, Subscription
from bot.handlers.language_handler import all_provinces
from bot.bot_instance import bot
from bot.utils.state_manager import user_states, file_path

PROVINCES_PER_PAGE = 8
PROCEDURES_PER_PAGE = 8
OFFICES_PER_PAGE = 8


###############################################################################
#                       ФУНКЦИИ РАБОТЫ С БД
###############################################################################
def add_subscription_sqlalchemy(
        user_id,
        telegram_id,
        telegram_handle,
        phone_number,
        service_name,
        province,
        procedure,
        addresses,
        subscription_days
):
    """
    Сохраняет подписку в БД (SQLAlchemy).
    """
    session = SessionLocal()
    try:
        # Проверяем, есть ли уже пользователь
        user = session.query(User).filter_by(telegram_id=str(user_id)).first()
        if not user:
            user = User(telegram_id=str(user_id))
            session.add(user)
            session.commit()

        now = datetime.datetime.now()
        expires = now + datetime.timedelta(days=subscription_days)

        subscription = Subscription(
            user_id=user.user_id,
            telegram_id=telegram_id,
            service_name=service_name,
            province=province,
            procedure=procedure,
            addresses=addresses,  # ARRAY(String) в модели
            purchase_date=now,
            expiration_date=expires,
            status='active'
        )
        session.add(subscription)
        session.commit()
        return subscription
    finally:
        session.close()


###############################################################################
#                       СТАРТ ПОДПИСКИ
###############################################################################
@bot.message_handler(commands=['add_subscription'])
def add_subscription_command(message):
    """
    Начинаем оформление подписки.
    """
    user_states[message.chat.id] = {}
    show_province_page(message.chat.id, 0)


###############################################################################
#                      ВЫБОР ПРОВИНЦИИ
###############################################################################
def get_province_page(page=0):
    """
    Возвращает часть списка провинций для пагинации.
    """
    start = page * PROVINCES_PER_PAGE
    end = start + PROVINCES_PER_PAGE
    return all_provinces[start:end]


def show_province_page(chat_id, page=0):
    """
    Показывает список провинций, удаляя предыдущее сообщение.
    """
    # Удаляем старое сообщение
    if chat_id in user_states and "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    provinces_menu = InlineKeyboardMarkup(row_width=2)
    provinces = get_province_page(page)
    # Кнопки провинций
    buttons = [
        InlineKeyboardButton(prov, callback_data=f"choose_province|{prov}")
        for prov in provinces
    ]
    provinces_menu.add(*buttons)

    # Кнопка «➡️ Далее», если ещё есть
    if (page + 1) * PROVINCES_PER_PAGE < len(all_provinces):
        provinces_menu.add(
            InlineKeyboardButton("➡️ Далее", callback_data=f"province_next|{page + 1}")
        )

    sent_message = bot.send_message(chat_id, "📍 Выберите провинцию:", reply_markup=provinces_menu)

    user_states.setdefault(chat_id, {})
    user_states[chat_id]["last_message_id"] = sent_message.message_id
    return sent_message


@bot.callback_query_handler(func=lambda call: call.data.startswith("province_next"))
def province_next_page(call):
    """
    Листаем список провинций вперёд.
    """
    chat_id = call.message.chat.id
    page = int(call.data.split("|")[-1])

    # Удаляем старое сообщение
    if chat_id in user_states and "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    show_province_page(chat_id, page)


@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_province"))
def choose_province(call):
    """
    Пользователь выбрал провинцию. Сохраняем и переходим к выбору процедур.
    """
    chat_id = call.message.chat.id
    _, province = call.data.split("|")
    telegram_id = call.from_user.id
    user_states[chat_id] = {"province": province}
    session = SessionLocal()
    try:
        # Проверяем, есть ли пользователь в базе
        user = session.query(User).filter_by(telegram_id=str(telegram_id)).first()
        if not user:
            # Создаем нового пользователя
            user = User(telegram_id=str(telegram_id))
            session.add(user)
            session.commit()

    finally:
        session.close()

    # Обновляем user_states
    if chat_id not in user_states:
        user_states[chat_id] = {}  # Создаём запись, если её не было

    user_states[chat_id]["province"] = province
    user_states[chat_id]["telegram_id"] = telegram_id  # Теперь всегда записываем telegram_id

    # Удаляем старое сообщение
    if "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    sent_message = show_procedures_page(chat_id, 0)
    user_states[chat_id]["last_message_id"] = sent_message.message_id


###############################################################################
#                      ВЫБОР ПРОЦЕДУРЫ
###############################################################################
def get_procedures_by_province(province_name):
    """
    Получает список процедур (словарей) по провинции из config.json.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    province_data = data.get(province_name, {})
    procedures = []
    for category in ["tramites_oficinas_extranjeria", "tramites_policia_nacional"]:
        if category in province_data:
            procedures.extend(province_data[category])
    return procedures


def get_procedures_page(province_name, page=0):
    """
    Возвращает "кусок" процедур для пагинации.
    """
    all_procedures = get_procedures_by_province(province_name)
    start = page * PROCEDURES_PER_PAGE
    end = start + PROCEDURES_PER_PAGE
    return all_procedures[start:end]


def show_procedures_page(chat_id, page=0):
    """
    Показывает список процедур, удаляя старое сообщение.
    """
    # Удаляем старое сообщение
    if chat_id in user_states and "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    province = user_states.get(chat_id, {}).get("province")
    if not province:
        return bot.send_message(chat_id, "⚠️ Ошибка: провинция не выбрана.")

    procedures = get_procedures_page(province, page)
    if not procedures:
        return bot.send_message(chat_id, f"❌ Нет доступных процедур для {province}.")

    procedures_menu = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(
            proc["nombre"],
            callback_data=f"choose_procedure|{proc['valor']}"
        )
        for proc in procedures
        if isinstance(proc, dict) and "nombre" in proc and "valor" in proc
    ]
    if not buttons:
        return bot.send_message(chat_id, "⚠️ Ошибка: не удалось загрузить процедуры.")

    procedures_menu.add(*buttons)

    # Пагинация
    all_p = get_procedures_by_province(province)
    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"procedures_prev|{page - 1}"))
    if (page + 1) * PROCEDURES_PER_PAGE < len(all_p):
        nav_btns.append(InlineKeyboardButton("➡️ Далее", callback_data=f"procedures_next|{page + 1}"))
    if nav_btns:
        procedures_menu.add(*nav_btns)

    # Кнопка «Назад к выбору провинции»
    procedures_menu.add(InlineKeyboardButton("🔙 Назад к выбору провинции", callback_data="back_to_provinces"))

    text = f"📌 Вы выбрали провинцию: {province}\n📝 Выберите процедуру:"
    sent_message = bot.send_message(chat_id, text, reply_markup=procedures_menu)

    user_states[chat_id]["last_message_id"] = sent_message.message_id
    return sent_message


@bot.callback_query_handler(func=lambda call: call.data.startswith("procedures_prev"))
def procedures_prev_page(call):
    """Пагинация процедур: назад."""
    chat_id = call.message.chat.id
    page = int(call.data.split("|")[-1])

    if chat_id in user_states and "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    show_procedures_page(chat_id, page)


@bot.callback_query_handler(func=lambda call: call.data.startswith("procedures_next"))
def procedures_next_page(call):
    """Пагинация процедур: вперёд."""
    chat_id = call.message.chat.id
    page = int(call.data.split("|")[-1])

    if chat_id in user_states and "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    show_procedures_page(chat_id, page)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_provinces")
def back_to_provinces(call):
    """Возврат к списку провинций."""
    chat_id = call.message.chat.id

    # Удаляем текущее сообщение (список процедур)
    if chat_id in user_states and "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    show_province_page(chat_id, 0)


###############################################################################
#                     ВЫБОР ОФИСА/АДРЕСА ПОСЛЕ ПРОЦЕДУРЫ
###############################################################################
def get_offices_for_procedure(province_name, procedure_val):
    """
    Заглушка: возвращает список офисов (словарей) для данной провинции и процедуры.
    Пока просто мок-данные.
    """
    # В реальности можно хранить в JSON, или генерировать
    # Здесь вернём пару офисов с уникальными 'id'
    return [
        {"id": "oficina_1", "name": "Oficina Extranjería #1"},
        {"id": "oficina_2", "name": "Oficina Extranjería #2"},
        {"id": "oficina_3", "name": "Comisaría Policía - Toma de Huellas"}
    ]


def show_offices_page(chat_id):
    """
    Показываем пользователю список офисов, плюс кнопку «Все отделения».
    """
    # Удаляем старое сообщение
    if chat_id in user_states and "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    province = user_states[chat_id].get("province")
    procedure_val = user_states[chat_id].get("procedure_val", "(не выбрано)")

    offices = get_offices_for_procedure(province, procedure_val)

    offices_menu = InlineKeyboardMarkup(row_width=1)

    # Кнопка "Все отделения"
    offices_menu.add(InlineKeyboardButton("✅ Все отделения", callback_data="offices_all"))

    # Добавляем конкретные офисы
    for office in offices:
        offices_menu.add(
            InlineKeyboardButton(
                f"🏢 {office['name']}",
                callback_data=f"choose_office|{office['id']}"
            )
        )

    # Кнопка «Назад к выбору процедур»
    offices_menu.add(
        InlineKeyboardButton("⬅️ Назад к выбору процедуры", callback_data="back_to_procedures_list")
    )

    text = (
        f"Выбрана процедура: {procedure_val}\n"
        f"Пожалуйста, выберите нужное вам отделение для процедуры в {province}:\n\n"
        "Если вам нужна запись на более раннюю дату, выберите конкретное отделение.\n"
        "Или нажмите 'Все отделения'."
    )

    sent_message = bot.send_message(
        chat_id,
        text,
        reply_markup=offices_menu
    )
    user_states[chat_id]["last_message_id"] = sent_message.message_id
    return sent_message


@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_procedure"))
def choose_procedure(call):
    """
    Пользователь выбрал конкретную процедуру, сохраняем и переходим к выбору офисов.
    """
    chat_id = call.message.chat.id
    _, procedure_val = call.data.split("|")

    # Сохраняем процедуру
    user_states[chat_id]["procedure_val"] = procedure_val

    # Удаляем предыдущее сообщение (список процедур)
    if "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    # Переходим к выбору офисов
    sent_message = show_offices_page(chat_id)
    user_states[chat_id]["last_message_id"] = sent_message.message_id


@bot.callback_query_handler(func=lambda call: call.data == "offices_all")
def offices_all_handler(call):
    """
    Пользователь выбрал "Все отделения".
    """
    chat_id = call.message.chat.id
    user_states[chat_id]["addresses"] = ["ALL_OFFICES"]

    # Удаляем текущее сообщение (список офисов)
    if "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    # Переходим к выбору тарифа
    select_subscription_plan(chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_office"))
def choose_office_handler(call):
    """
    Пользователь выбрал конкретный офис,
    сохраняем его в addresses и переходим к тарифу.
    """
    chat_id = call.message.chat.id
    _, office_id = call.data.split("|")

    # Сохраняем выбор офиса
    user_states[chat_id]["addresses"] = [office_id]

    # Удаляем текущее сообщение
    if "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    # Дальше выбор тарифа
    select_subscription_plan(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_procedures_list")
def back_to_procedures_list_handler(call):
    """
    Возвращаемся к списку процедур из списка офисов.
    """
    chat_id = call.message.chat.id
    # Удаляем текущее сообщение (список офисов)
    if "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    sent_message = show_procedures_page(chat_id, 0)
    user_states[chat_id]["last_message_id"] = sent_message.message_id


###############################################################################
#                    ВЫБОР ТАРИФА -> ОФОРМЛЕНИЕ ПОДПИСКИ
###############################################################################
def select_subscription_plan(chat_id):
    """
    Показываем кнопки: 7 дней, 14 дней, 30 дней.
    (Вместо старых ask_all_addresses)
    """
    # Удаляем старое сообщение, если нужно
    if chat_id in user_states and "last_message_id" in user_states[chat_id]:
        try:
            bot.delete_message(chat_id, user_states[chat_id]["last_message_id"])
        except:
            pass

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⭐ 750 на 7 дней", callback_data="sub_7"),
        InlineKeyboardButton("👍 1500 на 14 дней", callback_data="sub_14"),
        InlineKeyboardButton("📅 2500 на 30 дней", callback_data="sub_30")
    )
    sent_message = bot.send_message(chat_id, "Выберите ваш вариант подписки:", reply_markup=markup)

    user_states.setdefault(chat_id, {})
    user_states[chat_id]["last_message_id"] = sent_message.message_id


def escape_markdown(text):
    """Экранирует спецсимволы для Markdown."""
    return re.sub(r'([_*[\]()~`>#+-=|{}.!])', r'\\\1', text)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def finalize_subscription(call):
    """
    Пользователь выбрал срок подписки (7, 14, 30 дней).
    """
    chat_id = call.message.chat.id
    try:
        days_str = call.data.split("_")[1]
        days = int(days_str)

        data = user_states.get(chat_id, {})
        if not data:
            bot.send_message(chat_id, "⚠️ Ошибка: данные подписки не найдены. Попробуйте снова (/add_subscription).")
            return

        expiration_date = (datetime.datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        print(f"DEBUG: user_states[{chat_id}] = {user_states.get(chat_id, {})}")
        print(f"DEBUG: telegram_id = {user_states.get(chat_id, {}).get('telegram_id')}")
        telegram_id = user_states.get(chat_id, {}).get("telegram_id")
        if not telegram_id:
            telegram_id = call.from_user.id  # Берём ID из Telegram, если его нет в user_states
            user_states[chat_id]["telegram_id"] = telegram_id  # Сохраняем его в user_states

        added_sub = add_subscription_sqlalchemy(
            user_id=chat_id,
            telegram_id=str(telegram_id),
            telegram_handle=f"@{call.from_user.username}" if call.from_user.username else "",
            phone_number="",
            service_name=f"{days} дневная подписка",
            province=data.get('province', 'Не указано'),
            procedure=data.get('procedure_val', 'Не указано'),
            addresses=data.get('addresses', ['ALL_OFFICES']),
            subscription_days=days,
        )

        bot.send_message(
            chat_id,
            "✅ *Подписка оформлена* 🎉\n\n"
            f"📌 *Процедура:* {escape_markdown(data.get('procedure_val', 'не указано'))}\n"
            f"📍 *Провинция:* {escape_markdown(data.get('province', 'Не указано'))}\n"
            f"🏢 *Отделение:* {escape_markdown(', '.join(data.get('addresses', ['ALL_OFFICES'])))}\n"
            f"📅 *Подписка действует до:* {escape_markdown(expiration_date)}\n\n"
            "_Спасибо за использование нашего сервиса_",
            parse_mode="MarkdownV2"
        )

        # Очищаем состояние
        user_states.pop(chat_id, None)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
