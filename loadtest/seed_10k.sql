-- Seed 10,000 total users (9,998 synthetic customers + 2 existing users),
-- 20,000 orders, 40,000 order items, and 10,000 table reservations for load testing.
BEGIN;

-- 1. Seed 9,998 users (85% email verified, 15% unverified per Hybrid policy)
INSERT INTO users (name, email, password_hash, role, phone, email_verified_at, created_at, search_text)
SELECT
    'Khách hàng #' || i,
    'user_' || lpad(i::text, 5, '0') || '@dateno.vn',
    '$argon2id$v=19$m=65536,t=3,p=4$loadtestseedplaceholderhash$loadtestseedplaceholderhashvalue',
    'CUSTOMER',
    '091' || lpad(i::text, 7, '0'),
    CASE WHEN (i % 20) < 17 THEN now() - (i || ' minutes')::interval ELSE NULL END,
    now() - (i || ' minutes')::interval,
    'khach hang #' || i || ' user_' || lpad(i::text, 5, '0') || '@dateno.vn 091' || lpad(i::text, 7, '0')
FROM generate_series(1, 9998) AS s(i)
ON CONFLICT (email) DO NOTHING;

-- 2. Seed 20,000 orders distributed across the seeded users
WITH seeded_users AS (
    SELECT id, name, phone, row_number() OVER (ORDER BY id) AS rn
    FROM users
    WHERE email LIKE 'user_%@dateno.vn'
)
INSERT INTO orders (
    user_id, subtotal_price, discount_amount, total_price,
    status, payment_method, payment_status,
    location_id, delivery_name, delivery_phone, delivery_address, delivery_note, created_at
)
SELECT
    u.id,
    625000,
    0,
    625000,
    (ARRAY['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'])[1 + (g % 4)],
    (ARRAY['COD', 'MOMO'])[1 + (g % 2)],
    CASE WHEN (g % 2) = 1 THEN 'PAID' ELSE 'UNPAID' END,
    1 + (g % 3),
    u.name,
    u.phone,
    'Số ' || (1 + (g % 500)) || ' Đường Nguyễn Huệ, Quận 1, TP.HCM',
    '',
    now() - ((g * 2) || ' minutes')::interval
FROM generate_series(1, 20000) AS g
JOIN seeded_users u ON u.rn = 1 + ((g - 1) % 9998);

-- 3. Seed 2 order_items per seeded order (40,000 order_items)
WITH seeded_orders AS (
    SELECT o.id
    FROM orders o
    JOIN users u ON u.id = o.user_id
    WHERE u.email LIKE 'user_%@dateno.vn'
)
INSERT INTO order_items (order_id, product_id, price_at_purchase, quantity)
SELECT
    so.id,
    1 + ((so.id + item_no) % 20),
    312500,
    1
FROM seeded_orders so
CROSS JOIN generate_series(1, 2) AS item_no;

-- 4. Seed 10,000 reservations across the seeded users
WITH seeded_users AS (
    SELECT id, name, phone, row_number() OVER (ORDER BY id) AS rn
    FROM users
    WHERE email LIKE 'user_%@dateno.vn'
)
INSERT INTO reservations (
    user_id, location_id, customer_name, customer_phone,
    reservation_date, reservation_time, guest_count, special_requests, status, created_at
)
SELECT
    u.id,
    1 + (g % 3),
    u.name,
    u.phone,
    CURRENT_DATE + ((g % 30) - 10),
    '19:00:00'::time,
    2 + (g % 6),
    '',
    (ARRAY['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'])[1 + (g % 4)],
    now() - ((g * 3) || ' minutes')::interval
FROM generate_series(1, 10000) AS g
JOIN seeded_users u ON u.rn = 1 + ((g - 1) % 9998);

ANALYZE;
COMMIT;
