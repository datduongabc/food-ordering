<?php

use PHPUnit\Framework\TestCase;

require_once ROOT_PATH . '/app/modules/auth/auth_service.php';
require_once ROOT_PATH . '/app/modules/auth/auth_model.php';

class AuthModuleTest extends TestCase
{
    private AuthService $authService;
    private AuthModel $authModel;

    protected function setUp(): void
    {
        $_SESSION = [];
        $_COOKIE = [];
        TestDatabaseHelper::setup();
        $this->authService = new AuthService();
        $this->authModel = new AuthModel();
    }

    public function testSignUpValidationAndSuccess(): void
    {
        // Empty fields
        $res = $this->authService->signUpLogic('', 'test@mail.com', 'password123', '0912345678');
        $this->assertFalse($res['success']);

        // Invalid email
        $res = $this->authService->signUpLogic('John', 'not-an-email', 'password123', '0912345678');
        $this->assertFalse($res['success']);

        // Duplicate email
        $res = $this->authService->signUpLogic('John', 'customer1@dateno.com', 'password123', '0999888777');
        $this->assertFalse($res['success']);
        $this->assertStringContainsString('Email already registered', $res['message']);

        // Duplicate phone
        $res = $this->authService->signUpLogic('John', 'unique@dateno.com', 'password123', '0901234561');
        $this->assertFalse($res['success']);
        $this->assertStringContainsString('Phone number already registered', $res['message']);

        // Short password
        $res = $this->authService->signUpLogic('John', 'unique@dateno.com', '12345', '0999888777');
        $this->assertFalse($res['success']);

        // Invalid phone
        $res = $this->authService->signUpLogic('John', 'unique@dateno.com', 'password123', '123abc');
        $this->assertFalse($res['success']);

        // Happy path
        $res = $this->authService->signUpLogic('John Doe', 'john.doe@dateno.com', 'password123', '0988776655');
        $this->assertTrue($res['success']);
    }

    public function testSignInValidationAndSuccess(): void
    {
        // Empty fields
        $this->assertFalse($this->authService->signInLogic('', '')['success']);

        // Short password
        $this->assertFalse($this->authService->signInLogic('customer1@dateno.com', 'short')['success']);

        // Wrong password
        $this->assertFalse($this->authService->signInLogic('customer1@dateno.com', 'wrongpassword')['success']);

        // Non-existent user
        $this->assertFalse($this->authService->signInLogic('nobody@dateno.com', 'password123')['success']);

        // Valid login
        $res = $this->authService->signInLogic('customer1@dateno.com', 'password123');
        $this->assertTrue($res['success']);
        $this->assertSame('Customer One', $res['userInfo']['name']);
        $this->assertSame('CUSTOMER', $res['userInfo']['role']);
    }

    public function testRememberMeAndTokenAutoLoginAndRevoke(): void
    {
        $plainToken = bin2hex(random_bytes(32));
        $hashToken = hash('sha256', $plainToken);

        $saved = $this->authModel->saveTokenData(1, $hashToken, 'REMEMBER_ME', 60);
        $this->assertTrue($saved);

        // Valid auto-login
        $autoRes = $this->authService->signInWithToken($plainToken);
        $this->assertTrue($autoRes['success']);
        $this->assertSame('customer1@dateno.com', $autoRes['userInfo']['email']);

        // Invalid token auto-login
        $badRes = $this->authService->signInWithToken('invalid_plain_token');
        $this->assertFalse($badRes['success']);

        // Revoke token
        $revoked = $this->authService->revokeToken($plainToken);
        $this->assertTrue($revoked['success']);
    }

    public function testTokenValidationVerifyEmailAndPasswordReset(): void
    {
        $email = 'customer1@dateno.com';
        $plainToken = bin2hex(random_bytes(32));
        $hashToken = hash('sha256', $plainToken);

        $this->authModel->saveTokenData(1, $hashToken, 'FORGOT_PASSWORD', 15);

        // Non-existent user validation
        $this->assertFalse($this->authService->validateToken('missing@dateno.com', $plainToken, 'FORGOT_PASSWORD')['success']);

        // Wrong token increments attempts
        $wrong = $this->authService->validateToken($email, 'wrong_token', 'FORGOT_PASSWORD');
        $this->assertFalse($wrong['success']);
        $this->assertSame(1, (int)$this->authModel->getAttempts(1, 'FORGOT_PASSWORD')['attempts']);

        // Correct token succeeds
        $valid = $this->authService->validateToken($email, $plainToken, 'FORGOT_PASSWORD');
        $this->assertTrue($valid['success']);

        // Max attempts check
        for ($i = 0; $i < 5; $i++) {
            $this->authModel->incrementAttempts(1, 'FORGOT_PASSWORD');
        }
        $locked = $this->authService->validateToken($email, $plainToken, 'FORGOT_PASSWORD');
        $this->assertFalse($locked['success']);
        $this->assertSame('Too many attempts.', $locked['message']);

        // Reset password
        $this->assertFalse($this->authService->createNewPassword($email, 'short', 'FORGOT_PASSWORD')['success']);
        $resetOk = $this->authService->createNewPassword($email, 'newStrongPass99', 'FORGOT_PASSWORD');
        $this->assertTrue($resetOk['success']);

        // Verify can sign in with new password
        $loginNew = $this->authService->signInLogic($email, 'newStrongPass99');
        $this->assertTrue($loginNew['success']);

        // Email verification logic
        $this->authModel->saveTokenData(1, $hashToken, 'EMAIL_VERIFICATION', 15);
        $verifyRes = $this->authService->verifyEmailLogic($email);
        $this->assertTrue($verifyRes['success']);

        // Get user by ID
        $userInfo = $this->authService->getUserInfoById(1);
        $this->assertSame($email, $userInfo['email']);

        // Initiate secure process edge cases
        $this->assertFalse($this->authService->initiateSecureProcess('', 'FORGOT_PASSWORD')['success']);
        $this->assertFalse($this->authService->initiateSecureProcess('nonexistent@dateno.com', 'FORGOT_PASSWORD')['success']);
    }
}
