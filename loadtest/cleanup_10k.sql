-- Remove synthetic 10k load-test dataset while preserving real accounts and data.
BEGIN;

DELETE FROM orders
WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'user_%@dateno.vn');

DELETE FROM reservations
WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'user_%@dateno.vn');

DELETE FROM users
WHERE email LIKE 'user_%@dateno.vn';

ANALYZE;
COMMIT;
