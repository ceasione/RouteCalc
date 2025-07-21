
SELECT calculation_id,
       composer_intent,
       composer_url,
       composer_ip,
       composer_phone,
       composer_blacklisted
FROM tg_message
WHERE chat_id = :chat_id AND message_id = :message_id;
