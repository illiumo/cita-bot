from bot.bot_instance import bot
from database.setup import SessionLocal
from database.models import Subscription
from collections import defaultdict
from bot.utils.state_manager import file_path as filepath
import json
import telebot
import re


def escape_markdown_v2(text):
    """Экранирует спецсимволы для MarkdownV2, но не экранирует дефисы и пробелы."""
    escape_chars = r'_*[\]()~`>#+=|{}.!'  # Исключаем дефис `-`
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def get_active_subscriptions():
    """Получает все активные подписки с telegram_id, province, procedure"""
    session = SessionLocal()
    try:
        active_subs = session.query(Subscription.telegram_id, Subscription.province, Subscription.procedure) \
            .filter(Subscription.status == 'active') \
            .all()

        print(f"🔍 Найдено подписок: {len(active_subs)}")  # Отладка
        if not active_subs:
            print("⚠️ Нет активных подписок в базе данных.")
        else:
            print(active_subs)  # Выведет сами записи

        return active_subs
    finally:
        session.close()


def get_procedure_name(procedure_id):
    """Ищет полное название процедуры в config.json по её ID."""
    if not procedure_id:
        return "Неизвестная процедура"

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)

        for province in data.values():
            for category in ["tramites_oficinas_extranjeria", "tramites_policia_nacional"]:
                for procedure in province.get(category, []):
                    if procedure.get("valor") == procedure_id:
                        return procedure.get("nombre")  # Возвращаем полное название

        return procedure_id  # Если не нашли, оставляем ID
    except Exception as e:
        print(f"⚠️ Ошибка при чтении config.json: {e}")
        return procedure_id


def group_subscriptions_by_province_and_procedure():
    """Группирует подписки по провинции и процедуре."""
    subscriptions = get_active_subscriptions()
    grouped = defaultdict(lambda: defaultdict(set))  # {province: {procedure: {telegram_id}}}

    if not subscriptions:
        print("⚠️ Нет подписок для обработки.")
        return grouped

    for telegram_id, province, procedure in subscriptions:
        if not province or not procedure:
            print(f"⚠️ Ошибка: Подписка {telegram_id} имеет пустые данные и была пропущена.")
            continue

        grouped[province][procedure].add(telegram_id)

    print(f"✅ DEBUG: grouped_data = {dict(grouped)}")  # Отладка структуры grouped_data
    return grouped


def send_notifications(grouped_data):
    """
    Отправляет уведомления пользователям.
    grouped_data — это { "province": { "procedure": {telegram_id, telegram_id} } }
    """
    if not grouped_data:
        print("⚠️ Нет новых записей для уведомлений.")
        return

    print("📢 Начинаем отправку уведомлений...")
    for province, procedures in grouped_data.items():
        for procedure_id, telegram_ids in procedures.items():
            procedure_name = get_procedure_name(procedure_id)  # Получаем полное название процедуры

            # Экранируем спецсимволы перед отправкой
            province_escaped = escape_markdown_v2(province)
            procedure_name_escaped = escape_markdown_v2(procedure_name)

            message = (
                f"🔥 *{procedure_name_escaped}* \\({province_escaped}\\) 🔥\n\n"
                f"✅ Запись на процедуру *{procedure_name_escaped}* сейчас доступна!\n"
                f"📅 В регионе *{province_escaped}* появились доступные даты.\n\n"
                f"🔗 *Перейдите по ссылке для записи:*\n"
                f"[Нажмите здесь](https://icp.administracionelectronica.gob.es/icpplus/citar?p=33&locale=es)\n\n"
                f"⏳ *Поспешите, места ограничены!*"
            )

            for telegram_id in telegram_ids:
                print(f"📩 Отправка сообщения пользователю: {telegram_id}")
                try:
                    bot.send_message(telegram_id, message, parse_mode="MarkdownV2", disable_web_page_preview=True)
                    print(f"✅ Уведомление отправлено {telegram_id}")
                except telebot.apihelper.ApiTelegramException as e:
                    print(f"❌ Ошибка при отправке {telegram_id}: {e}")
                    if "can't parse entities" in str(e):
                        print(f"⚠️ Ошибка парсинга MarkdownV2. Провинция: {province}, Процедура: {procedure_name}")
                        print(f"🔄 Попытка отправки без форматирования...")
                        fallback_message = (
                            f"🔥 {procedure_name} ({province}) 🔥\n\n"
                            f"✅ Запись на процедуру {procedure_name} сейчас доступна!\n"
                            f"📅 В регионе {province} появились доступные даты.\n\n"
                            f"🔗 Перейдите по ссылке для записи:\n"
                            f"https://icp.administracionelectronica.gob.es/icpplus/citar?p=33&locale=es\n\n"
                            f"⏳ Поспешите, места ограничены!"
                        )
                        bot.send_message(telegram_id, fallback_message, parse_mode=None, disable_web_page_preview=True)
                    elif "chat not found" in str(e):
                        print(f"⚠️ Ошибка: Пользователь {telegram_id} не найден (возможно, заблокировал бота).")
                    else:
                        print(f"❌ Ошибка при отправке {telegram_id}: {e}")


def check_and_notify_users():
    """Основной процесс: получаем подписки, группируем и отправляем уведомления."""
    grouped_data = group_subscriptions_by_province_and_procedure()
    send_notifications(grouped_data)


# Запускаем процесс проверки и отправки
check_and_notify_users()
