-- ============================================================================
-- PostgreSQL Schema & Seed Data for DaTeNO Restaurant (food_ordering_db)
-- Automatically imported on container startup via /docker-entrypoint-initdb.d/
-- ============================================================================

SET client_encoding = 'UTF8';

DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS reservations CASCADE;
DROP TABLE IF EXISTS product_availabilities CASCADE;
DROP TABLE IF EXISTS password_resets CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. Table: users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'CUSTOMER' CHECK (role IN ('CUSTOMER', 'ADMIN')),
    phone CHAR(10) NOT NULL UNIQUE,
    is_email_verified SMALLINT DEFAULT 0,
    email_verified_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL
);

-- 2. Table: categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL
);

-- 3. Table: locations
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    url TEXT NOT NULL
);

-- 4. Table: products
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category_id INT NULL REFERENCES categories(id) ON DELETE SET NULL,
    image_url VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    average_rating NUMERIC(3, 2) DEFAULT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL
);

-- 5. Table: product_availabilities
CREATE TABLE product_availabilities (
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    location_id INT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, location_id)
);

-- 6. Table: cart_items
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity SMALLINT DEFAULT 1
);

-- 7. Table: orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED')),
    payment_method VARCHAR(20) NOT NULL DEFAULT 'COD' CHECK (payment_method IN ('COD', 'MOMO')),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'UNPAID' CHECK (payment_status IN ('UNPAID', 'PAID', 'FAILED', 'REFUNDED')),
    momo_order_id VARCHAR(100) NULL DEFAULT NULL,
    momo_trans_id VARCHAR(100) NULL DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. Table: order_items
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    price_at_purchase NUMERIC(10, 2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0
);

-- 9. Table: password_resets
CREATE TABLE password_resets (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token CHAR(64) NOT NULL,
    type VARCHAR(30) DEFAULT NULL CHECK (type IN ('FORGOT_PASSWORD', 'REMEMBER_ME', 'EMAIL_VERIFICATION', 'CHANGE_PASSWORD')),
    expired_at TIMESTAMP DEFAULT NULL,
    attempts SMALLINT DEFAULT 0 CHECK (attempts <= 5),
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL
);

-- 10. Table: reservations
CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    user_id INT DEFAULT NULL REFERENCES users(id) ON DELETE SET NULL,
    location_id INT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(255) NOT NULL,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    guest_count SMALLINT NOT NULL DEFAULT 1,
    special_requests TEXT,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED')),
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP NULL DEFAULT NULL
);

-- 11. Table: reviews
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    rating SMALLINT DEFAULT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Seed Data Import
-- ============================================================================

INSERT INTO categories (id, name, slug, created_at, updated_at, deleted_at) VALUES
(1, 'Starters', 'starters', '2026-04-16 06:22:59', '2026-04-16 06:22:59', NULL),
(2, 'Main Dishes', 'main_dishes', '2026-04-16 06:22:59', '2026-04-19 03:56:29', NULL);

INSERT INTO locations (id, name, address, url) VALUES
(1, 'Ascent Restaurant - District 1', '123 Le Loi Street, Ben Thanh Ward, District 1, Ho Chi Minh City', 'https://maps.app.goo.gl/District1Branch'),
(2, 'Ascent Restaurant - District 7', '456 Nguyen Van Linh Street, Tan Phong Ward, District 7, Ho Chi Minh City', 'https://maps.app.goo.gl/District7Branch'),
(3, 'Ascent Restaurant - Thu Duc', '789 Vo Van Ngan Street, Linh Chieu Ward, Thu Duc City, Ho Chi Minh City', 'https://maps.app.goo.gl/ThuDucBranch');

INSERT INTO products (id, category_id, image_url, name, description, price, average_rating, slug, created_at, deleted_at) VALUES
(1, 1, 'caesar_salad.webp', 'Classic Caesar Salad', 'Crisp romaine lettuce tossed in house-made creamy Caesar dressing. Topped with buttery croutons, aged Parmesan, and black pepper. A refreshing light start.', 12.50, 4.50, 'caesar-salad', '2026-04-16 06:27:39', NULL),
(2, 1, 'crab_corn_chicken_soup.webp', 'Crab, Corn & Chicken Soup', 'Thick Asian-style soup with fresh crab meat, sweet corn, and tender chicken. Simmered in rich broth and finished with a hint of sesame oil for a warm palate.', 10.00, NULL, 'crab-corn-chicken-soup', '2026-04-16 06:27:39', NULL),
(3, 1, 'fish_sauce_chicken_wings.webp', 'Fish Sauce Chicken Wings', 'Golden fried chicken wings glazed in a savory and sweet garlic-infused fish sauce reduction. A perfect balance of salty and tangy flavors with a crispy finish.', 14.50, NULL, 'fish-sauce-chicken-wings', '2026-04-16 06:27:39', NULL),
(4, 1, 'french_onion_soup.webp', 'French Onion Soup', 'Rich, slow-simmered onion broth topped with toasted artisan baguette and a thick layer of melted, bubbly Gruyere cheese. A classic Parisian comfort dish.', 11.00, NULL, 'french-onion-soup', '2026-04-16 06:27:39', NULL),
(5, 1, 'garlic_butter_bread.webp', 'Garlic Butter Bread', 'Artisan baguette slices toasted with house-blended garlic butter made from premium butter, roasted garlic, and fresh parsley. Irresistibly crunchy and savory.', 6.00, NULL, 'garlic-butter-bread', '2026-04-16 06:27:39', NULL),
(6, 1, 'herb_potato_wedges.webp', 'Herb Potato Wedges', 'Thick-cut potato wedges roasted with Mediterranean herbs like rosemary and thyme. Crispy on the outside and fluffy inside. Served with spicy garlic mayo.', 8.50, NULL, 'herb-potato-wedges', '2026-04-16 06:27:39', NULL),
(7, 1, 'nha_trang_grilled_pork.webp', 'Nha Trang Grilled Pork', 'Skewers of lean pork marinated in lemongrass and local spices, grilled over charcoal for a smoky aroma. Served with traditional peanut dipping sauce.', 15.00, NULL, 'nha-trang-grilled-pork', '2026-04-16 06:27:39', NULL),
(8, 1, 'papaya_salad_dried_beef.webp', 'Papaya Salad with Dried Beef', 'Crunchy green papaya and aromatic herbs tossed in zesty lime vinaigrette. Topped with savory dried beef and roasted peanuts for an explosion of textures.', 13.00, NULL, 'papaya-salad-dried-beef', '2026-04-16 06:27:39', NULL),
(9, 1, 'seafood_spring_rolls_mayo.webp', 'Seafood Spring Rolls with Mayo', 'Crispy spring rolls stuffed with premium shrimp, squid, and taro. Served with a smooth, tangy Japanese mayonnaise dipping sauce for a rich seafood experience.', 12.00, NULL, 'seafood-spring-rolls-mayo', '2026-04-16 06:27:39', NULL),
(10, 1, 'seaweed_flying_fish_roe_salad.webp', 'Seaweed & Roe Salad', 'Nutrient-rich chilled seaweed marinated in sesame oil and vinegar. Topped with crunchy flying fish roe that pops with every bite. Fresh and nutty flavor.', 14.00, NULL, 'seaweed-roe-salad', '2026-04-16 06:27:39', NULL),
(11, 1, 'shrimp_pork_spring_rolls.webp', 'Shrimp & Pork Spring Rolls', 'Fresh rice paper rolls with poached tiger prawns, pork belly, vermicelli, and fresh mint. Served with a rich hoisin-peanut dipping sauce. Light and healthy.', 9.50, NULL, 'shrimp-pork-spring-rolls', '2026-04-16 06:27:39', NULL),
(12, 1, 'silken_tofu_pork_floss_salted_egg.webp', 'Silken Tofu with Salted Egg', 'Velvety smooth silken tofu topped with rich salted egg yolk sauce, premium pork floss, and scallion oil. A unique contrast of cool tofu and savory toppings.', 10.50, 5.00, 'silken-tofu-salted-egg', '2026-04-16 06:27:39', NULL),
(13, 2, 'bbq_grilled_pork_ribs.webp', 'BBQ Grilled Pork Ribs', 'Fall-off-the-bone tender baby back ribs glazed in smoky hickory BBQ sauce. Grilled over an open flame and served with creamy coleslaw and buttered corn.', 28.00, 5.00, 'bbq-grilled-pork-ribs', '2026-04-16 06:27:39', NULL),
(14, 2, 'beef_steak_red_wine.webp', 'Beef Steak in Red Wine', 'Premium center-cut beef tenderloin seared to perfection and drizzled with a luxurious Cabernet Sauvignon reduction. Served with garlic mashed potatoes.', 35.00, 5.00, 'beef-steak-red-wine', '2026-04-16 06:27:39', NULL),
(15, 2, 'chicken_breast_rolled_with_mushrooms_in_cream_sauce.webp', 'Mushroom Cream Chicken Roll', 'Chicken breast rolled with sautéed wild mushrooms and herbs, oven-baked and smothered in a velvety Chardonnay cream sauce. Served with roasted vegetables.', 24.50, NULL, 'mushroom-cream-chicken', '2026-04-16 06:27:39', NULL),
(16, 2, 'crispy_fried_noodles_with_seafood.webp', 'Crispy Seafood Fried Noodles', 'Bird’s nest crispy egg noodles topped with stir-fried tiger prawns, squid, and seasonal vegetables in a savory ginger-soy gravy. A delightful mix of textures.', 18.00, NULL, 'crispy-seafood-noodles', '2026-04-16 06:27:39', NULL),
(17, 2, 'crispy_fried_stuffed_squid.webp', 'Crispy Stuffed Squid', 'Large fresh squid stuffed with seasoned minced pork and wood-ear mushrooms, fried until golden. Served with sweet chili sauce and fresh cucumbers.', 22.00, NULL, 'crispy-stuffed-squid', '2026-04-16 06:27:39', NULL),
(18, 2, 'german_braised_pork_knuckle.webp', 'German Braised Pork Knuckle', 'Authentic Bavarian pork knuckle braised in dark beer and roasted until skin is crackling crisp. Served with sauerkraut, potato dumplings, and rich gravy.', 32.00, 5.00, 'german-pork-knuckle', '2026-04-16 06:27:39', NULL),
(19, 2, 'grilled_chicken_with_wild_honey.webp', 'Wild Honey Grilled Chicken', 'Half chicken marinated in wild mountain honey and garden herbs, grilled slowly for caramelized skin and juicy meat. Served with jasmine rice and ginger sauce.', 20.00, NULL, 'wild-honey-grilled-chicken', '2026-04-16 06:27:39', NULL),
(20, 2, 'herb_grilled_lamb.webp', 'Herb Grilled Lamb Chops', 'Premium lamb chops marinated in rosemary and extra virgin olive oil. Char-broiled and served with mint jelly, roasted root vegetables, and red wine jus.', 38.00, NULL, 'herb-grilled-lamb', '2026-04-16 06:27:39', NULL),
(21, 2, 'hong_kong_style_steamed_sea_bass.webp', 'HK Style Steamed Sea Bass', 'Fresh sea bass steamed with julienned ginger and scallions. Finished with sizzling premium soy sauce and hot peanut oil to release aromatic flavors.', 30.00, 5.00, 'hk-steamed-sea-bass', '2026-04-16 06:27:39', NULL),
(22, 2, 'pan_seared_salmon_with_passion_fruit_sauce.webp', 'Passion Fruit Salmon', 'Pan-seared Atlantic salmon fillet with crispy skin and flaky center. Balanced by a bright passion fruit reduction. Served on baby spinach and quinoa.', 29.50, NULL, 'passion-fruit-salmon', '2026-04-16 06:27:39', NULL),
(23, 2, 'peking_roast_duck.webp', 'Peking Roast Duck', 'World-famous delicacy with thin, honey-glazed crispy skin. Served with warm handmade pancakes, scallions, cucumbers, and sweet hoisin dipping sauce.', 45.00, 4.50, 'peking-roast-duck', '2026-04-16 06:27:39', NULL),
(24, 2, 'royal_seafood_fried_rice.webp', 'Royal Seafood Fried Rice', 'Fragrant jasmine rice stir-fried with shrimp, squid, and scallops. Infused with natural golden turmeric and topped with crispy shallots and scallions.', 16.50, NULL, 'royal-seafood-fried-rice', '2026-04-16 06:27:39', NULL),
(25, 2, 'seafood_cheese_pizza.webp', 'Seafood Cheese Pizza', 'Stone-baked thin crust pizza topped with San Marzano tomato sauce, Mozzarella, tiger prawns, and squid rings. Finished with dried oregano and chili flakes.', 19.00, NULL, 'seafood-cheese-pizza', '2026-04-16 06:27:39', NULL),
(26, 2, 'shaking_beef_with_french_fries.webp', 'Shaking Beef with Fries', 'Premium beef tenderloin cubes wok-tossed with red onions and a savory soy-butter glaze. Served with fresh salad and crispy golden-brown French fries.', 26.00, NULL, 'shaking-beef-fries', '2026-04-16 06:27:39', NULL),
(27, 2, 'spaghetti_bolognese.webp', 'Classic Spaghetti Bolognese', 'Al dente spaghetti smothered in a deep, rich meat sauce slow-simmered for eight hours with premium beef and vine-ripened tomatoes. Topped with parmesan.', 15.50, NULL, 'spaghetti-bolognese', '2026-04-16 06:27:39', NULL),
(28, 2, 'steamed_giant_prawns_with_coconut_water.webp', 'Coconut Steamed Prawns', 'Jumbo tiger prawns steamed inside a fresh young coconut to infuse natural sweetness. Served with a zesty green chili and lime dipping sauce.', 25.00, NULL, 'coconut-steamed-prawns', '2026-04-16 06:27:39', NULL),
(29, 2, 'thai_green_chicken_curry.webp', 'Thai Green Chicken Curry', 'Aromatic and spicy classic curry with tender chicken, coconut milk, lemongrass, and Thai basil. Best enjoyed with fragrant jasmine rice.', 18.50, NULL, 'thai-green-curry', '2026-04-16 06:27:39', NULL),
(30, 2, 'thai_spicy_and_sour_seafood_hot_pot.webp', 'Thai Spicy Seafood Hot Pot', 'Grand pot of spicy Tom Yum broth packed with tiger prawns, squid, and fish. A perfect balance of spicy, sour, and savory flavors designed for sharing.', 42.00, 3.00, 'thai-seafood-hotpot', '2026-04-16 06:27:39', NULL);

INSERT INTO product_availabilities (product_id, location_id)
SELECT p.id, l.id FROM products p CROSS JOIN locations l;

-- Reset initial product ratings since reviews table starts empty
UPDATE products SET average_rating = NULL;

-- Initial Admin Account (Email: datduongtandat385@gmail.com | Password: 12345678)
INSERT INTO users (id, name, email, password, role, phone, is_email_verified, email_verified_at, created_at, deleted_at) VALUES
(1, 'Administrator', 'datduongtandat385@gmail.com', '$2y$10$abcdefghijklmnopqrstuu6VFZE.TtiJ2cr5lBUZZkdTY8FkA5ul2', 'ADMIN', '0819152362', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL);

-- ============================================================================
-- PostgreSQL Triggers
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_after_order_item_insert()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE orders
    SET total_price = total_price + (NEW.price_at_purchase * NEW.quantity)
    WHERE id = NEW.order_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_order_item_insert
AFTER INSERT ON order_items
FOR EACH ROW
EXECUTE FUNCTION fn_after_order_item_insert();

CREATE OR REPLACE FUNCTION fn_after_review_insert()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET average_rating = (SELECT ROUND(AVG(rating)::numeric, 2) FROM reviews WHERE product_id = NEW.product_id)
    WHERE id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_review_insert
AFTER INSERT ON reviews
FOR EACH ROW
EXECUTE FUNCTION fn_after_review_insert();

-- ============================================================================
-- Sync SERIAL Sequences to max(id)
-- ============================================================================
SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));
SELECT setval(pg_get_serial_sequence('categories', 'id'), COALESCE((SELECT MAX(id) FROM categories), 1));
SELECT setval(pg_get_serial_sequence('locations', 'id'), COALESCE((SELECT MAX(id) FROM locations), 1));
SELECT setval(pg_get_serial_sequence('products', 'id'), COALESCE((SELECT MAX(id) FROM products), 1));
SELECT setval(pg_get_serial_sequence('orders', 'id'), COALESCE((SELECT MAX(id) FROM orders), 1));
SELECT setval(pg_get_serial_sequence('order_items', 'id'), COALESCE((SELECT MAX(id) FROM order_items), 1));
SELECT setval(pg_get_serial_sequence('password_resets', 'id'), COALESCE((SELECT MAX(id) FROM password_resets), 1));
SELECT setval(pg_get_serial_sequence('reservations', 'id'), COALESCE((SELECT MAX(id) FROM reservations), 1));
SELECT setval(pg_get_serial_sequence('reviews', 'id'), COALESCE((SELECT MAX(id) FROM reviews), 1));
