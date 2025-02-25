from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from database.setup import Base


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, nullable=False)
    subscriptions = relationship('Subscription', back_populates='user')


class Subscription(Base):
    __tablename__ = 'subscriptions'
    subscription_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    service_name = Column(String, nullable=False)
    province = Column(String, nullable=False)
    procedure = Column(String, nullable=False)
    addresses = Column(ARRAY(String), nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    user = relationship('User', back_populates='subscriptions')


class SubscriptionIndex(Base):
    __tablename__ = 'subscriptions_index'
    index_id = Column(Integer, primary_key=True, index=True)
    province = Column(String, nullable=False)
    procedure = Column(String, nullable=False)
    addresses = Column(ARRAY(String), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
