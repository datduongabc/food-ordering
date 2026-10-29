<?php

require_once ROOT_PATH . '/app/modules/order/order_model.php';

/**
 * MoMo Payment Gateway v2 Service
 * Implements MoMo HMAC-SHA256 signature generation, USD-to-VND conversion,
 * payment intent creation, and Return URL / IPN Webhook verification.
 */
class MomoService
{
    private OrderModel $orderModel;
    private string $partnerCode;
    private string $accessKey;
    private string $secretKey;
    private string $endpoint;
    private int $exchangeRate;

    public function __construct(?OrderModel $orderModel = null)
    {
        $this->orderModel = $orderModel ?? new OrderModel();
        $this->partnerCode = trim((string)($_ENV['MOMO_PARTNER_CODE'] ?? getenv('MOMO_PARTNER_CODE') ?: 'MOMOBKUN20180529'));
        $this->accessKey = trim((string)($_ENV['MOMO_ACCESS_KEY'] ?? getenv('MOMO_ACCESS_KEY') ?: 'klm05TvNBzhg7h7j'));
        $this->secretKey = trim((string)($_ENV['MOMO_SECRET_KEY'] ?? getenv('MOMO_SECRET_KEY') ?: 'at67qH6mk8w5Y1nAyMoYKMWACiEi2bsa'));
        $this->endpoint = trim((string)($_ENV['MOMO_ENDPOINT'] ?? getenv('MOMO_ENDPOINT') ?: 'https://test-payment.momo.vn/v2/gateway/api/create'));
        $rate = (int)($_ENV['MOMO_EXCHANGE_RATE'] ?? getenv('MOMO_EXCHANGE_RATE') ?: 25000);
        $this->exchangeRate = $rate > 0 ? $rate : 25000;
    }

    /**
     * Convert USD order total to VND integer amount within MoMo limits (1,000 - 50,000,000 VND)
     */
    public function convertUsdToVnd(float $usdAmount): int
    {
        $vnd = (int)round($usdAmount * $this->exchangeRate);
        return max(1000, min(50000000, $vnd));
    }

    /**
     * Format VND amount (e.g., "312,500 VND")
     */
    public function formatVnd(int $vndAmount): string
    {
        return number_format($vndAmount, 0, '.', ',') . ' VND';
    }

    /**
     * Generate MoMo v2 HMAC-SHA256 signature for payment creation
     */
    public function generateCreateSignature(array $params): string
    {
        $rawHash = "accessKey=" . ($params['accessKey'] ?? $this->accessKey)
            . "&amount=" . $params['amount']
            . "&extraData=" . ($params['extraData'] ?? '')
            . "&ipnUrl=" . $params['ipnUrl']
            . "&orderId=" . $params['orderId']
            . "&orderInfo=" . $params['orderInfo']
            . "&partnerCode=" . ($params['partnerCode'] ?? $this->partnerCode)
            . "&redirectUrl=" . $params['redirectUrl']
            . "&requestId=" . $params['requestId']
            . "&requestType=" . ($params['requestType'] ?? 'captureWallet');

        return hash_hmac('sha256', $rawHash, $this->secretKey);
    }

    /**
     * Generate HMAC-SHA256 verification signature for return/callback validation
     */
    public function generateCallbackSignature(int $orderId, string $momoOrderId, int $amountVnd, int $resultCode): string
    {
        $raw = "accessKey={$this->accessKey}&amount={$amountVnd}&orderId={$momoOrderId}&partnerCode={$this->partnerCode}&resultCode={$resultCode}&internalOrderId={$orderId}";
        return hash_hmac('sha256', $raw, $this->secretKey);
    }

    /**
     * Create a MoMo payment session for a customer's order
     */
    public function createPaymentIntent(int $userId, int $orderId, string $baseUrl = 'http://localhost:8000'): array
    {
        $order = $this->orderModel->getOrderByIdAndUser($orderId, $userId);
        if (!$order) {
            return [
                'success' => false,
                'message' => 'Order not found or access denied.'
            ];
        }

        if (($order['payment_status'] ?? 'UNPAID') === 'PAID') {
            return [
                'success' => false,
                'message' => "Order #{$orderId} has already been paid."
            ];
        }

        if ($order['status'] === 'CANCELLED') {
            return [
                'success' => false,
                'message' => "Order #{$orderId} is cancelled and cannot be paid."
            ];
        }

        $amountUsd = (float)$order['total_price'];
        $amountVnd = $this->convertUsdToVnd($amountUsd);
        $momoOrderId = 'DATENO_' . $orderId . '_' . time();
        $requestId = $momoOrderId . '_REQ';
        $orderInfo = "DaTeNO Restaurant - Payment for Order #{$orderId}";
        $extraData = base64_encode((string)json_encode(['order_id' => $orderId, 'user_id' => $userId]));

        $redirectUrl = rtrim($baseUrl, '/') . '/index.php?page=orders&action=momo_return';
        $ipnUrl = rtrim($baseUrl, '/') . '/index.php?page=orders&action=momo_ipn';
        $requestType = 'captureWallet';

        $payload = [
            'partnerCode' => $this->partnerCode,
            'partnerName' => 'DaTeNO Restaurant',
            'storeId'     => 'DaTeNO_Store_01',
            'requestId'   => $requestId,
            'amount'      => $amountVnd,
            'orderId'     => $momoOrderId,
            'orderInfo'   => $orderInfo,
            'redirectUrl' => $redirectUrl,
            'ipnUrl'      => $ipnUrl,
            'lang'        => 'en',
            'extraData'   => $extraData,
            'requestType' => $requestType,
        ];

        $signature = $this->generateCreateSignature($payload + ['accessKey' => $this->accessKey]);
        $payload['signature'] = $signature;

        // Record the initiated MoMo order ID on the order
        $this->orderModel->attachMomoOrderId($orderId, $momoOrderId);

        $successSignature = $this->generateCallbackSignature($orderId, $momoOrderId, $amountVnd, 0);
        $cancelSignature = $this->generateCallbackSignature($orderId, $momoOrderId, $amountVnd, 1006);

        return [
            'success'           => true,
            'sandbox'           => app_is_local(),
            'order'             => $order,
            'order_id'          => $orderId,
            'momo_order_id'     => $momoOrderId,
            'request_id'        => $requestId,
            'partner_code'      => $this->partnerCode,
            'amount_usd'        => $amountUsd,
            'amount_vnd'        => $amountVnd,
            'amount_vnd_label'  => $this->formatVnd($amountVnd),
            'exchange_rate'     => $this->exchangeRate,
            'order_info'        => $orderInfo,
            'request_signature' => $signature,
            'success_signature' => $successSignature,
            'cancel_signature'  => $cancelSignature,
            'endpoint'          => $this->endpoint,
            'payload'           => $payload,
        ];
    }

    /**
     * Verify MoMo callback/return parameters and update order payment & fulfillment status
     */
    public function handleCallback(int $userId, array $params): array
    {
        $orderId = (int)($params['internal_order_id'] ?? 0);
        $momoOrderId = trim((string)($params['orderId'] ?? ''));
        $amountVnd = (int)($params['amount'] ?? 0);
        $resultCode = isset($params['resultCode']) ? (int)$params['resultCode'] : -1;
        $providedSig = trim((string)($params['signature'] ?? ''));
        $transId = trim((string)($params['transId'] ?? ('MOMO' . random_int(100000000, 999999999))));

        if ($orderId <= 0 && preg_match('/^DATENO_(\d+)_/', $momoOrderId, $matches)) {
            $orderId = (int)$matches[1];
        }

        if ($orderId <= 0 || $momoOrderId === '') {
            return [
                'success' => false,
                'message' => 'Invalid MoMo payment callback parameters.'
            ];
        }

        $order = $this->orderModel->getOrderByIdAndUser($orderId, $userId);
        if (!$order) {
            return [
                'success' => false,
                'message' => 'Order not found for payment verification.'
            ];
        }

        $expectedSig = $this->generateCallbackSignature($orderId, $momoOrderId, $amountVnd, $resultCode);
        if ($providedSig === '' || !hash_equals($expectedSig, $providedSig)) {
            return [
                'success' => false,
                'message' => 'Invalid MoMo HMAC-SHA256 payment signature.'
            ];
        }

        if ($resultCode === 0) {
            $updated = $this->orderModel->markOrderPaid($orderId, $momoOrderId, $transId);
            if (!$updated) {
                return [
                    'success' => false,
                    'message' => 'Failed to update order payment status.'
                ];
            }

            return [
                'success'       => true,
                'order_id'      => $orderId,
                'momo_order_id' => $momoOrderId,
                'trans_id'      => $transId,
                'message'       => "MoMo Payment successful (Transaction #{$transId})! Order #{$orderId} is now PAID & CONFIRMED."
            ];
        }

        $this->orderModel->markOrderPaymentFailed($orderId, $momoOrderId);
        return [
            'success'       => false,
            'order_id'      => $orderId,
            'momo_order_id' => $momoOrderId,
            'message'       => "MoMo Payment for Order #{$orderId} was cancelled or declined (Code: {$resultCode}). You can retry payment anytime from My Orders."
        ];
    }
}
