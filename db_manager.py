import json
import os
import datetime

DB_FILE = "database.json"


def load_db():
    if not os.path.exists(DB_FILE):
        # Если файла нет, возвращаем структуру по умолчанию
        return {"users": [], "subscriptions_index": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_db(db_data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        # ensure_ascii=False -> чтобы писать в utf-8
        json.dump(db_data, f, indent=4, ensure_ascii=False)


def create_or_update_subscription_index(db_data, user_id, province, procedure, address):
    """
    Записывает user_id в subscriptions_index для указанной комбинации.
    """
    key = f"{province}|{procedure}|{address}"
    if key not in db_data['subscriptions_index']:
        db_data['subscriptions_index'][key] = []
    if user_id not in db_data['subscriptions_index'][key]:
        db_data['subscriptions_index'][key].append(user_id)


def remove_from_subscription_index(db_data, user_id, province, procedure, address):
    """
    Удаляет user_id из subscriptions_index, если подписка больше не активна.
    """
    key = f"{province}|{procedure}|{address}"
    if key in db_data['subscriptions_index']:
        if user_id in db_data['subscriptions_index'][key]:
            db_data['subscriptions_index'][key].remove(user_id)
        # Если список опустел, можем удалить ключ совсем (не обязательно)
        if not db_data['subscriptions_index'][key]:
            del db_data['subscriptions_index'][key]


def add_subscription(user_id, telegram_handle, phone_number,
                     service_name, province, procedure,
                     addresses, subscription_days=7):
    """
    Добавляет подписку пользователю (создаёт пользователя, если его нет).
    Если addresses = ['ALL'], значит подписка на все адреса.
    """
    now = datetime.datetime.now()
    expires = now + datetime.timedelta(days=subscription_days)

    db_data = load_db()

    # 1. Находим пользователя или создаём нового
    user_record = None
    for user in db_data['users']:
        if user['user_id'] == user_id:
            user_record = user
            break
    if not user_record:
        user_record = {
            "user_id": user_id,
            "telegram_handle": telegram_handle,
            "phone_number": phone_number,
            "subscriptions": []
        }
        db_data['users'].append(user_record)

    # 2. Создаём новую подписку
    subscription_data = {
        "service_name": service_name,
        "province": province,
        "procedure": procedure,
        "addresses": addresses,  # либо ['ALL'], либо список
        "purchase_date": now.isoformat(timespec='minutes'),
        "subscription_expires": expires.isoformat(timespec='minutes'),
        "status": "active"
    }
    user_record['subscriptions'].append(subscription_data)

    # 3. Обновляем subscriptions_index
    for addr in addresses:
        create_or_update_subscription_index(db_data, user_id, province, procedure, addr)

    # 4. Сохраняем базу
    save_db(db_data)
    return subscription_data


def deactivate_subscription(user_id, province, procedure, addresses):
    """
    Снимает подписку (меняет статус на 'expired' или 'canceled' — по ситуации)
    и убирает user_id из индекса.
    """
    db_data = load_db()
    for user in db_data['users']:
        if user['user_id'] == user_id:
            for sub in user['subscriptions']:
                if (sub['province'] == province and
                        sub['procedure'] == procedure and
                        sub['addresses'] == addresses and
                        sub['status'] == 'active'):
                    sub['status'] = 'canceled'
                    # Удаляем пользователя из индекса
                    for addr in addresses:
                        remove_from_subscription_index(db_data, user_id, province, procedure, addr)
            break
    save_db(db_data)
