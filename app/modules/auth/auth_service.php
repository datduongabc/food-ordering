<?php

require_once ROOT_PATH . '/app/modules/auth/auth_model.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

class AuthService
{
    private $authModel;
    const MAX_ATTEMPTS = 5;
    const TTL_REMEMBER_TOKEN = 10080; // 7 days in minutes
    const TTL_SECURE_TOKEN = 15;      // 15 minutes

    public function __construct()
    {
        $this->authModel = new AuthModel();
    }

    // Helper function: Send email to user (returns true if sent via SMTP, false if fallback needed)
    private function sendUniversalEmail($receiver, $token, $type): bool
    {
        $mailEmail = trim((string)($_ENV['MAIL_EMAIL'] ?? getenv('MAIL_EMAIL') ?: ''));
        $rawPassword = trim((string)($_ENV['MAIL_PASSWORD'] ?? getenv('MAIL_PASSWORD') ?: ''));
        $mailPassword = str_replace(' ', '', $rawPassword);

        // Gmail SMTP strictly requires a 16-character alphanumeric Google App Password.
        // Skip blocking SMTP connection if credentials are missing or use a regular account password.
        if (
            empty($mailEmail) ||
            $mailEmail === 'no-reply@dateno.com' ||
            !preg_match('/^[a-zA-Z0-9]{16}$/', $mailPassword)
        ) {
            return false;
        }

        $mail = new PHPMailer(true);

        try {
            // --- SMTP Server Configuration ---
            $mail->isSMTP();
            $mail->Host       = 'smtp.gmail.com';
            $mail->SMTPAuth   = true;
            $mail->Username   = $mailEmail;
            $mail->Password   = $mailPassword;
            $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
            $mail->Port       = 587;
            $mail->Timeout    = 4;
            $mail->CharSet    = 'UTF-8';

            // --- Sender & Receiver ---
            $mail->setFrom($mailEmail, 'DaTeNO Restaurant');
            $mail->addAddress($receiver);

            $emailContent = match ($type) {
                'FORGOT_PASSWORD' => [
                    'subject' => 'Reset Your Password - DaTeNO',
                    'title'   => 'Password Reset Request',
                    'desc'    => 'Please use the token below to reset your password:'
                ],
                'EMAIL_VERIFICATION' => [
                    'subject' => 'Verify Your Account - DaTeNO',
                    'title'   => 'Account Verification',
                    'desc'    => 'Please use the token below to activate your account:'
                ],
                'CHANGE_PASSWORD' => [
                    'subject' => 'Security Alert: Password Change',
                    'title'   => 'Confirm Password Change',
                    'desc'    => 'Use this token to confirm you want to change your password:'
                ],
                default => [
                    'subject' => 'Security Token - DaTeNO',
                    'title'   => 'Security Verification',
                    'desc'    => 'Use the token below for your request:'
                ]
            };

            // --- Email Body Template ---
            $mail->isHTML(true);
            $mail->Subject = $emailContent['subject'];
            $mail->Body    = "
            <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;'>
                <div style='background-color: #0d9488; padding: 20px; text-align: center; color: white;'>
                    <h1 style='margin: 0;'>DaTeNO Restaurant</h1>
                </div>
                <div style='padding: 30px; line-height: 1.6; color: #374151;'>
                    <h2 style='color: #111827;'>{$emailContent['title']}</h2>
                    <p>{$emailContent['desc']}</p>
                    <div style='text-align: center; margin: 30px 0;'>
                        <span style='font-size: 20px; font-weight: bold; color: #0d9488; letter-spacing: 2px; background: #f0fdfa; padding: 10px 20px; border-radius: 4px; border: 1px dashed #0d9488; word-break: break-all; display: inline-block;'>
                            $token
                        </span>
                    </div>
                    <p style='font-size: 14px; color: #6b7280;'>This token will expire in 15 minutes.</p>
                    <p style='font-size: 14px; color: #6b7280;'>If you did not request this, please ignore this email.</p>
                </div>
                <div style='background-color: #f9fafb; padding: 15px; text-align: center; font-size: 12px; color: #9ca3af;'>
                    &copy; 2026 DaTeNO Restaurant. All rights reserved.
                </div>
            </div>
        ";

            $mail->send();
            return true;
        } catch (Exception $e) {
            error_log("PHPMailer Error: {$mail->ErrorInfo}");
            return false;
        }
    }

    // Sign up logic
    public function signUpLogic($name, $email, $password, $phone)
    {
        if (empty($name) || empty($email) || empty($password) || empty($phone)) {
            return [
                'success' => false,
                'message' => 'Please enter all fields.'
            ];
        }

        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return [
                'success' => false,
                'message' => 'Invalid email format.'
            ];
        }

        // Checking unique email and phone number
        $duplicate = $this->authModel->checkDuplicateInfo($email, $phone);

        if ($duplicate) {
            if ($duplicate['email'] === $email) {
                return [
                    'success' => false,
                    'message' => 'Email already registered.'
                ];
            }

            if ($duplicate['phone'] === $phone) {
                return [
                    'success' => false,
                    'message' => 'Phone number already registered.'
                ];
            }
        }

        if (strlen($password) < 8) {
            return [
                'success' => false,
                'message' => 'Password must be at least 8 characters long.'
            ];
        }

        if (strlen($phone) !== 10 || !ctype_digit($phone)) {
            return [
                'success' => false,
                'message' => 'Invalid phone number. Must be exactly 10 digits.'
            ];
        }

        $create_user = $this->authModel->createNewUser(
            $name,
            $email,
            password_hash($password, PASSWORD_DEFAULT),
            $phone
        );

        if (!$create_user) {
            return [
                'success' => false,
                'message' => 'Internal server error. Please try again.'
            ];
        }

        return [
            'success' => true,
            'message' => 'Sign up successful. Please sign in to continue.'
        ];
    }

    // Sign in logic
    public function signInLogic($email, $password)
    {
        if (empty($email) || empty($password)) {
            return [
                'success' => false,
                'message' => 'Please enter all fields.'
            ];
        }

        if (strlen($password) < 8) {
            return [
                'success' => false,
                'message' => 'Password must be at least 8 characters long.'
            ];
        }

        $user = $this->authModel->getUserRecord($email)['user_record'];

        if (!$user || !password_verify($password, $user["password"])) {
            return [
                'success' => false,
                'message' => 'Email or password is incorrect.'
            ];
        }

        return [
            'success' => true,
            'userInfo' => [
                'id' => $user['id'],
                'name' => $user['name'],
                'email' => $user['email'],
                'phone' => $user['phone'],
                'role' => $user['role'],
                'is_email_verified' => (int)$user['is_email_verified']
            ],
            "message" => "Signed in successfully."
        ];
    }

    public function rememberMeLogic($user_id)
    {
        $plain_token = bin2hex(random_bytes(32));
        $hash_token = hash('sha256', $plain_token);

        $this->authModel->saveTokenData($user_id, $hash_token, 'REMEMBER_ME', self::TTL_REMEMBER_TOKEN);

        setcookie('remember_me', $plain_token, time() + (7 * 24 * 60 * 60), "/", "", false, true);
    }

    public function signInWithToken($plain_token)
    {
        $hash_token = hash('sha256', $plain_token);
        $user = $this->authModel->autoLoginWithCookie($hash_token);

        if (!$user["success"] || !$user["user_record"]) {
            setcookie('remember_me', '', time() - 3600, "/");

            return [
                'success' => false,
                'message' => 'Session expired. Please login again.'
            ];
        }

        return [
            "success" => true,
            "userInfo" => [
                'id' => $user["user_record"]['id'],
                'name' => $user["user_record"]['name'],
                'email' => $user["user_record"]['email'],
                'phone' => $user["user_record"]['phone'],
                'role' => $user["user_record"]['role'],
                'is_email_verified' => (int)$user["user_record"]['is_email_verified']
            ],
            "message" => 'Automatically logged in.'
        ];
    }

    public function revokeToken($cookie_token)
    {
        $hash = hash('sha256', $cookie_token);
        $result = $this->authModel->deleteTokenByValue($hash, 'REMEMBER_ME');

        if (!$result) {
            return [
                "success" => false,
                "message" => "Internal server error."
            ];
        }

        return [
            "success" => true,
            "message" => "Logged out successfully."
        ];
    }

    public function initiateSecureProcess($email, $type)
    {
        if (empty($email) || empty($type)) {
            return [
                'success' => false,
                'message' => 'Please enter all fields.'
            ];
        }

        $user = $this->authModel->getUserRecord($email);

        if (!$user['user_record']) {
            return [
                'success' => false,
                'message' => 'No account found with that email address.'
            ];
        }

        $plain_token = bin2hex(random_bytes(32));
        $hash_token = hash('sha256', $plain_token);

        $save_token = $this->authModel->saveTokenData(
            $user["user_record"]["id"],
            $hash_token,
            $type,
            self::TTL_SECURE_TOKEN
        );

        if (!$save_token) {
            return [
                'success' => false,
                'message' => 'Internal server error while generating token.'
            ];
        }

        $sent = $this->sendUniversalEmail($email, $plain_token, $type);
        if (!$sent) {
            // SECURITY: displaying the token on screen lets anyone reset any account,
            // so this fallback is strictly limited to APP_ENV=local.
            if (!app_is_local()) {
                return [
                    'success' => false,
                    'message' => 'Could not send email. Please check SMTP configuration (MAIL_EMAIL / 16-char Google App Password).'
                ];
            }

            $_SESSION['dev_otp_token'] = $plain_token;
            $_SESSION['dev_otp_notice'] = 'Local Sandbox Mode (APP_ENV=local): SMTP is not configured, so the security token is shown here instead of being emailed:';
            return [
                'success' => true,
                'dev_fallback' => true,
                'token' => $plain_token,
                'message' => 'Security token generated (Local Sandbox Mode).'
            ];
        }

        unset($_SESSION['dev_otp_token'], $_SESSION['dev_otp_notice']);
        return [
            'success' => true,
            'message' => 'A security token has been sent to your email.'
        ];
    }

    public function validateToken($email, $plain_token, $type)
    {
        $user = $this->authModel->getUserRecord($email)['user_record'];

        if (!$user) {
            return [
                'success' => false,
                'message' => 'User not found.'
            ];
        }

        $attempts_data = $this->authModel->getAttempts($user['id'], $type);
        $attempts = $attempts_data ? (int)$attempts_data['attempts'] : 0;

        if ($attempts >= self::MAX_ATTEMPTS) {
            return [
                'success' => false,
                'message' => 'Too many attempts.'
            ];
        }

        $result = $this->authModel->getValidToken($user['id'], $type);

        if (!$result || !hash_equals($result['token'], hash('sha256', trim($plain_token)))) {
            $this->authModel->incrementAttempts($user['id'], $type);

            return [
                'success' => false,
                'message' => 'Invalid or expired token.'
            ];
        }

        unset($_SESSION['dev_otp_token'], $_SESSION['dev_otp_notice']);

        return [
            'success' => true,
            'message' => 'Token verified.'
        ];
    }

    public function verifyEmailLogic($email)
    {
        $result = $this->authModel->verifyEmail($email);

        if (!$result) {
            return [
                'success' => false,
                'message' => 'Internal server error.'
            ];
        }

        $user_data = $this->authModel->getUserRecord($email);
        if ($user_data['user_record']) {
            $this->authModel->deleteToken($user_data['user_record']['id'], 'EMAIL_VERIFICATION');
        }

        return [
            'success' => true,
            'message' => 'Email verified successfully.'
        ];
    }

    public function createNewPassword($email, $new_password, $type)
    {
        if (strlen($new_password) < 8) {
            return [
                'success' => false,
                'message' => 'Password must be at least 8 characters.'
            ];
        }

        $hash_password = password_hash($new_password, PASSWORD_DEFAULT);
        $result = $this->authModel->updatePassword($email, $hash_password);

        if (!$result) {
            return [
                'success' => false,
                'message' => 'Failed to update password.'
            ];
        }

        $user_record = $this->authModel->getUserRecord($email);
        if ($user_record['user_record']) {
            $this->authModel->deleteToken($user_record['user_record']['id'], $type);
            $this->authModel->deleteToken($user_record['user_record']['id'], 'REMEMBER_ME');
        }

        return [
            'success' => true,
            'message' => 'Password updated successfully.'
        ];
    }

    public function getUserInfoById($id)
    {
        $result = $this->authModel->getUserById($id);
        return $result['user_record'];
    }
}
