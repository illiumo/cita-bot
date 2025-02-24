CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    telegram_id TEXT UNIQUE NOT NULL
);