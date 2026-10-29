<?php

if (session_status() === PHP_SESSION_NONE) {
    @session_start();
}

if (!defined('ROOT_PATH')) {
    define('ROOT_PATH', dirname(__DIR__));
}

if (file_exists(ROOT_PATH . '/vendor/autoload.php')) {
    require_once ROOT_PATH . '/vendor/autoload.php';
}

require_once ROOT_PATH . '/app/core/Database.php';
require_once ROOT_PATH . '/app/core/Helpers.php';

/**
 * Helper class for setting up and resetting the test database schema & seed data
 * Works seamlessly with both PostgreSQL (in CI/Docker) and in-memory SQLite (local fast tests).
 */
class TestDatabaseHelper
{
    public static function setup(): PDO
    {
        $connType = getenv('DB_CONNECTION') ?: ($_ENV['DB_CONNECTION'] ?? 'sqlite');

        if ($connType === 'pgsql') {
            $dsn = sprintf(
                "pgsql:host=%s;port=%s;dbname=%s",
                getenv('DB_HOST') ?: 'localhost',
                getenv('DB_PORT') ?: '5432',
                getenv('DB_NAME') ?: 'food_ordering_db'
            );
            $pdo = new PDO(
                $dsn,
                getenv('DB_USER') ?: 'postgres',
                getenv('DB_PASSWORD') ?: 'postgres',
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false,
                ]
            );
            $sql = file_get_contents(ROOT_PATH . '/config/init_postgres.sql');
            $pdo->exec($sql);

            // Seed test fixture users & reviews for PHPUnit test suite
            $pdo->exec("TRUNCATE TABLE reviews, reservations, password_resets, order_items, orders, cart_items, users RESTART IDENTITY CASCADE;");
            $hash = password_hash('password123', PASSWORD_DEFAULT);
            $stmt = $pdo->prepare("
                INSERT INTO users (id, name, email, password, role, phone, is_email_verified) VALUES
                (1, 'Customer One', 'customer1@dateno.com', ?, 'CUSTOMER', '0901234561', 1),
                (2, 'Admin One', 'admin1@dateno.com', ?, 'ADMIN', '0901234562', 1)
            ");
            $stmt->execute([$hash, $hash]);
            $pdo->exec("
                SELECT setval(pg_get_serial_sequence('users', 'id'), 2);
                INSERT INTO reviews (user_id, product_id, rating, comment) VALUES
                (1, 1, 5, 'Delicious Caesar salad!'),
                (1, 13, 5, 'Amazing ribs!');
            ");

            Database::setConnection($pdo);
            return $pdo;
        }

        // In-memory SQLite database for standalone fast execution
        $pdo = new PDO('sqlite::memory:', null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
        $pdo->exec('PRAGMA foreign_keys = ON;');

        self::createSqliteSchema($pdo);
        self::seedSqliteData($pdo);

        Database::setConnection($pdo);
        return $pdo;
    }

    private static function createSqliteSchema(PDO $pdo): void
    {
        $pdo->exec("
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'CUSTOMER',
                phone TEXT NOT NULL UNIQUE,
                is_email_verified INTEGER DEFAULT 0,
                email_verified_at TEXT NULL DEFAULT NULL,
                created_at TEXT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT NULL DEFAULT NULL
            );

            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                created_at TEXT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT NULL DEFAULT NULL
            );

            CREATE TABLE locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                url TEXT NOT NULL
            );

            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NULL REFERENCES categories(id) ON DELETE SET NULL,
                image_url TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                average_rating NUMERIC(3, 2) DEFAULT NULL,
                slug TEXT NOT NULL UNIQUE,
                created_at TEXT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT NULL DEFAULT NULL
            );

            CREATE TABLE product_availabilities (
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
                PRIMARY KEY (product_id, location_id)
            );

            CREATE TABLE cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_Id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER DEFAULT 1
            );

            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                status TEXT DEFAULT 'PENDING',
                payment_method TEXT NOT NULL DEFAULT 'COD',
                payment_status TEXT NOT NULL DEFAULT 'UNPAID',
                momo_order_id TEXT NULL DEFAULT NULL,
                momo_trans_id TEXT NULL DEFAULT NULL,
                created_at TEXT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
                price_at_purchase NUMERIC(10, 2) NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token TEXT NOT NULL,
                type TEXT DEFAULT NULL,
                expired_at TEXT DEFAULT NULL,
                attempts INTEGER DEFAULT 0,
                created_at TEXT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT NULL DEFAULT NULL
            );

            CREATE TABLE reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT NULL REFERENCES users(id) ON DELETE SET NULL,
                location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                reservation_date TEXT NOT NULL,
                reservation_time TEXT NOT NULL,
                guest_count INTEGER NOT NULL DEFAULT 1,
                special_requests TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TEXT NULL DEFAULT CURRENT_TIMESTAMP,
                cancelled_at TEXT NULL DEFAULT NULL
            );

            CREATE TABLE reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                rating INTEGER DEFAULT NULL,
                comment TEXT,
                created_at TEXT NULL DEFAULT CURRENT_TIMESTAMP
            );
        ");
    }

    private static function seedSqliteData(PDO $pdo): void
    {
        $pdo->exec("
            INSERT INTO categories (id, name, slug) VALUES
            (1, 'Starters', 'starters'),
            (2, 'Main Dishes', 'main_dishes');

            INSERT INTO locations (id, name, address, url) VALUES
            (1, 'Ascent Restaurant - District 1', '123 Le Loi Street, District 1', 'https://maps.app.goo.gl/D1'),
            (2, 'Ascent Restaurant - District 7', '456 Nguyen Van Linh Street, District 7', 'https://maps.app.goo.gl/D7'),
            (3, 'Ascent Restaurant - Thu Duc', '789 Vo Van Ngan Street, Thu Duc', 'https://maps.app.goo.gl/TD');

            INSERT INTO products (id, category_id, image_url, name, description, price, average_rating, slug) VALUES
            (1, 1, 'caesar_salad.webp', 'Classic Caesar Salad', 'Crisp romaine lettuce with dressing.', 12.50, 4.80, 'caesar-salad'),
            (2, 1, 'french_onion_soup.webp', 'French Onion Soup', 'Rich slow-simmered onion broth.', 11.00, 4.50, 'french-onion-soup'),
            (13, 2, 'bbq_grilled_pork_ribs.webp', 'BBQ Grilled Pork Ribs', 'Fall-off-the-bone tender ribs.', 28.00, 5.00, 'bbq-grilled-pork-ribs');

            INSERT INTO product_availabilities (product_id, location_id) VALUES
            (1, 1), (1, 2), (2, 1), (13, 1), (13, 2), (13, 3);
        ");

        $hash = password_hash('password123', PASSWORD_DEFAULT);
        $stmt = $pdo->prepare("
            INSERT INTO users (id, name, email, password, role, phone, is_email_verified) VALUES
            (1, 'Customer One', 'customer1@dateno.com', ?, 'CUSTOMER', '0901234561', 1),
            (2, 'Admin One', 'admin1@dateno.com', ?, 'ADMIN', '0901234562', 1)
        ");
        $stmt->execute([$hash, $hash]);

        $pdo->exec("
            INSERT INTO reviews (user_id, product_id, rating, comment) VALUES
            (1, 1, 5, 'Delicious Caesar salad!'),
            (1, 13, 5, 'Amazing ribs!');
        ");
    }
}
