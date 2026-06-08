-- Buyurtma to'lov holati: to'lanmadi / to'landi (ish jarayoni statusidan alohida)
DO $$ BEGIN
    CREATE TYPE paymentstatus AS ENUM ('UNPAID', 'PAID');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS payment_status paymentstatus NOT NULL DEFAULT 'UNPAID';

-- Avvalgi to'langan buyurtmalarni migratsiya
UPDATE orders
SET payment_status = 'PAID'
WHERE status::text IN ('PAID', 'IS_PROCESS', 'READY', 'IN_PROGRESS', 'DELIVERED', 'RETURNED', 'vozvrat');
