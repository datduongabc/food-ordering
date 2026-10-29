<?php

session_start();

define('ROOT_PATH', dirname(__DIR__));

require_once ROOT_PATH . '/vendor/autoload.php';

if (getenv('DB_HOST') === false && file_exists(ROOT_PATH . '/.env')) {
    $dotenv = Dotenv\Dotenv::createImmutable(ROOT_PATH);
    $dotenv->safeLoad();
}

require_once ROOT_PATH . '/app/core/Database.php';
require_once ROOT_PATH . '/app/core/Helpers.php';
require_once ROOT_PATH . '/app/core/Router.php';

$router = new Router();
$router->dispatch();
