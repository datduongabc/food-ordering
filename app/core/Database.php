<?php
require_once __DIR__ . '/../../config/database.php';

class Database
{
    // Singleton Pattern
    private static $instance = null;
    private $pdo;

    private function __construct(?PDO $customPdo = null)
    {
        if ($customPdo !== null) {
            $this->pdo = $customPdo;
            return;
        }

        if (DB_CONNECTION === 'pgsql') {
            $dsn = "pgsql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";connect_timeout=5";
        } elseif (DB_CONNECTION === 'sqlite') {
            $dsn = "sqlite:" . DB_NAME;
        } else {
            $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4";
        }

        $options = [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
            PDO::ATTR_TIMEOUT            => 5,
        ];

        if (DB_CONNECTION !== 'sqlite') {
            $options[PDO::ATTR_PERSISTENT] = true;
        }

        try {
            if (DB_CONNECTION === 'sqlite') {
                $this->pdo = new PDO($dsn, null, null, $options);
            } else {
                $this->pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
            }
        } catch (PDOException $e) {
            throw new PDOException($e->getMessage(), (int)$e->getCode());
        }
    }

    public static function getInstance()
    {
        if (self::$instance === null) {
            self::$instance = new Database();
        }
        return self::$instance;
    }

    /**
     * Allow injecting a custom PDO connection (e.g. for PHPUnit testing)
     */
    public static function setConnection(?PDO $pdo): void
    {
        self::$instance = $pdo ? new Database($pdo) : null;
    }

    public function getConnection()
    {
        return $this->pdo;
    }

    public static function isPostgres(): bool
    {
        if (self::$instance && self::$instance->pdo) {
            return self::$instance->pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'pgsql';
        }
        return DB_CONNECTION === 'pgsql';
    }
}
