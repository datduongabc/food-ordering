<?php

use PHPUnit\Framework\TestCase;

class CoreAndHelpersTest extends TestCase
{
    private PDO $pdo;

    protected function setUp(): void
    {
        $_SESSION = [];
        $_POST = [];
        $_SERVER['REQUEST_METHOD'] = 'GET';
        $this->pdo = TestDatabaseHelper::setup();
    }

    public function testDatabaseSingletonAndDriverCheck(): void
    {
        $db = Database::getInstance();
        $this->assertInstanceOf(Database::class, $db);
        $this->assertSame($this->pdo, $db->getConnection());
        $this->assertIsBool(Database::isPostgres());
    }

    public function testBaseUrlAndHtmlEscapeAndFormatPrice(): void
    {
        $this->assertNotEmpty(base_url('css/style.css'));
        $this->assertNotEmpty(base_url(''));
        $this->assertSame('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;', e('<script>alert("x")</script>'));
        $this->assertSame('', e(null));
        $this->assertSame('$12.50', format_price(12.5));
        $this->assertSame('$0.00', format_price(0));
    }

    public function testCsrfFunctions(): void
    {
        $token = csrf_token();
        $this->assertSame(64, strlen($token));
        $this->assertSame($token, csrf_token());

        $fieldHtml = csrf_field();
        $this->assertStringContainsString('name="csrf_token"', $fieldHtml);
        $this->assertStringContainsString($token, $fieldHtml);

        // GET request always passes verify_csrf
        $_SERVER['REQUEST_METHOD'] = 'GET';
        $this->assertTrue(verify_csrf());

        // POST without token fails
        $_SERVER['REQUEST_METHOD'] = 'POST';
        $this->assertFalse(verify_csrf());

        // POST with wrong token fails
        $_POST['csrf_token'] = 'invalid_token';
        $this->assertFalse(verify_csrf());

        // POST with matching token succeeds
        $_POST['csrf_token'] = $token;
        $this->assertTrue(verify_csrf());
    }

    public function testGetCartCountForGuestAndLoggedInUser(): void
    {
        $this->assertSame(0, get_cart_count());

        // Guest cart
        $_SESSION['guest_cart'] = [1 => 2, 13 => 3];
        $this->assertSame(5, get_cart_count());

        // Logged-in user cart
        $_SESSION['user_id'] = 1;
        $this->assertSame(0, get_cart_count());

        $this->pdo->exec("INSERT INTO cart_items (user_Id, product_id, quantity) VALUES (1, 1, 4)");
        $this->assertSame(4, get_cart_count());
    }

    public function testAppIsLocalAndOtpFallbackIsDisabledInProduction(): void
    {
        $original = $_ENV['APP_ENV'] ?? null;

        $_ENV['APP_ENV'] = 'production';
        $this->assertFalse(app_is_local());

        // Without SMTP and outside local mode, the token must NOT be exposed on screen
        require_once ROOT_PATH . '/app/modules/auth/auth_service.php';
        $res = (new AuthService())->initiateSecureProcess('customer1@dateno.com', 'FORGOT_PASSWORD');
        $this->assertFalse($res['success']);
        $this->assertArrayNotHasKey('dev_otp_token', $_SESSION);

        $_ENV['APP_ENV'] = 'local';
        $this->assertTrue(app_is_local());
        $resLocal = (new AuthService())->initiateSecureProcess('customer1@dateno.com', 'FORGOT_PASSWORD');
        $this->assertTrue($resLocal['success']);
        $this->assertArrayHasKey('dev_otp_token', $_SESSION);

        if ($original === null) {
            unset($_ENV['APP_ENV']);
        } else {
            $_ENV['APP_ENV'] = $original;
        }
    }
}
