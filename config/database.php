<?php
define('DB_CONNECTION', trim($_ENV['DB_CONNECTION'] ?? getenv('DB_CONNECTION') ?: 'pgsql'));
define('DB_HOST', trim($_ENV['DB_HOST'] ?? getenv('DB_HOST') ?: 'localhost'));
define('DB_PORT', trim($_ENV['DB_PORT'] ?? getenv('DB_PORT') ?: (DB_CONNECTION === 'pgsql' ? '5432' : '3306')));
define('DB_NAME', trim($_ENV['DB_NAME'] ?? getenv('DB_NAME') ?: 'food_ordering_db'));
define('DB_USER', trim($_ENV['DB_USER'] ?? getenv('DB_USER') ?: 'postgres'));
define('DB_PASS', trim($_ENV['DB_PASSWORD'] ?? getenv('DB_PASSWORD') ?: 'postgres'));
