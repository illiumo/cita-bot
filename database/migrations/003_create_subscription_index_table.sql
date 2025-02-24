CREATE TABLE subscriptions_index (
    index_id SERIAL PRIMARY KEY,
    province TEXT NOT NULL,
    procedure TEXT NOT NULL,
    addresses TEXT[] NOT NULL,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_subscriptions_index_user_id ON subscriptions_index (user_id);
