CREATE TABLE subscriptions (
    subscription_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    telegram_id BIGINT NOT NULL,
    service_name TEXT NOT NULL,
    province TEXT NOT NULL,
    procedure TEXT NOT NULL,
    addresses TEXT[] NOT NULL,
    purchase_date TIMESTAMP NOT NULL,
    expiration_date TIMESTAMP NOT NULL,
    status TEXT NOT NULL
);
CREATE INDEX idx_subscriptions_user_id ON subscriptions (user_id);