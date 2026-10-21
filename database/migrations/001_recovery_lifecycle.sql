-- Brings an existing database in line with the recovery lifecycle:
-- PENDING -> NOTIFIED -> RECOVERED, or EXPIRED, with repeat abandonments allowed.
BEGIN;

UPDATE cart_recovery
SET recovery_status = 'PENDING'
WHERE recovery_status = 'DETECTED';

ALTER TABLE cart_recovery
    ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;

-- Replaced by a one-open-recovery-per-cart rule so a cart abandoned
-- again later can get a new recovery.
ALTER TABLE cart_recovery DROP CONSTRAINT IF EXISTS uq_cart_recovery_cart_id;
DROP INDEX IF EXISTS uq_cart_recovery_cart_id;

CREATE UNIQUE INDEX IF NOT EXISTS uq_cart_recovery_open_cart
    ON cart_recovery (cart_id)
    WHERE recovery_status = 'PENDING';

CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_recovery_id
    ON notifications (recovery_id);

COMMIT;
