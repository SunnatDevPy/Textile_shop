-- Add new payment enum value: cash
-- Run once in PostgreSQL before deploying code that writes payment='cash'.

ALTER TYPE payment ADD VALUE IF NOT EXISTS 'cash';
