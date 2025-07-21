
INSERT INTO tg_message (
    chat_id,
    message_id,
    calculation_id,
    message_body,
    composer_intent,
    composer_url,
    composer_ip,
    composer_phone,
    composer_blacklisted
) VALUES (
    :chat_id,
    :message_id,
    :calculation_id,
    :message_body,
    :composer_intent,
    :composer_url,
    :composer_ip,
    :composer_phone,
    :composer_blacklisted
)
