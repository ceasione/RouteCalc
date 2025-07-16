
SELECT calculation_id, message_body
FROM tg_messages
WHERE chat_id = :chat_id AND message_id = :message_id;
