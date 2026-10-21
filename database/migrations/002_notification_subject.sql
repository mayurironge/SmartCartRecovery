-- Recovery emails get a generated subject line, stored with the message.
ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS subject VARCHAR(255);
