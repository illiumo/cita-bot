from setup import SessionLocal
from models import User, Subscription, SubscriptionIndex

session = SessionLocal()

try:
    users = session.query(User).all()
    print("Users:")
    for user in users:
        print(f"- ID: {user.user_id}, Telegram ID: {user.telegram_id}, Subscriptions: {len(user.subscriptions)}")

    subscriptions = session.query(Subscription).all()
    print("\nSubscriptions:")
    for sub in subscriptions:
        print(f"- ID: {sub.subscription_id}, UserID: {sub.user_id}, Service: {sub.service_name}, Status: {sub.status}")

    subscription_indices = session.query(SubscriptionIndex).all()
    print("\nSubscription Index:")
    for sub_index in subscription_indices:
        print(f"- Index ID: {sub_index.index_id}, Province: {sub_index.province}, Procedure: {sub_index.procedure}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    session.close()
