CREATE TABLE IF NOT EXISTS tg_message (
    chat_id INTEGER,
    message_id INTEGER,
    calculation_id CHAR(40),
    message_body TEXT,
    composer_intent TEXT,
    composer_url TEXT,
    composer_ip TEXT,
    composer_phone TEXT,
    composer_blacklisted BOOLEAN,
    FOREIGN KEY (calculation_id) REFERENCES calculation(calculation_id),
    PRIMARY KEY (chat_id, message_id)
);