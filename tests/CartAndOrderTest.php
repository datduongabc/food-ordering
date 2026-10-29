<?php

use PHPUnit\Framework\TestCase;

require_once ROOT_PATH . '/app/modules/cart/cart_service.php';
require_once ROOT_PATH . '/app/modules/order/order_service.php';
require_once ROOT_PATH . '/app/modules/order/momo_service.php';
require_once ROOT_PATH . '/app/modules/order/admin_order_controller.php';

class CartAndOrderTest extends TestCase
{
    private CartService $cartService;
    private OrderService $orderService;

    protected function setUp(): void
    {
        $_SESSION = [];
        TestDatabaseHelper::setup();
        $this->cartService = new CartService();
        $this->orderService = new OrderService();
    }

    public function testGuestCartAndMergeToUserCart(): void
    {
        // Invalid product
        $this->assertFalse($this->cartService->addToCart(null, 0, 1)['success']);
        $this->assertFalse($this->cartService->addToCart(null, 9999, 1)['success']);

        // Add to guest cart
        $add1 = $this->cartService->addToCart(null, 1, 2);
        $this->assertTrue($add1['success']);
        $this->assertSame(2, $add1['cart_count']);

        $add2 = $this->cartService->addToCart(null, 13, 1);
        $this->assertTrue($add2['success']);
        $this->assertSame(3, $add2['cart_count']);

        $guestDetails = $this->cartService->getCartDetails(null);
        $this->assertCount(2, $guestDetails['items']);
        $this->assertEquals(53.00, $guestDetails['total_price']);

        // Update & remove in guest cart
        $this->cartService->updateQuantity(null, 1, 3);
        $this->assertSame(4, $this->cartService->getCartDetails(null)['total_count']);

        $this->cartService->updateQuantity(null, 13, 0);
        $this->assertCount(1, $this->cartService->getCartDetails(null)['items']);

        // Merge guest cart into logged-in user #1
        $this->cartService->mergeGuestCartToUser(1, $_SESSION['guest_cart']);
        $this->cartService->clearCart(null);

        $userCart = $this->cartService->getCartDetails(1);
        $this->assertCount(1, $userCart['items']);
        $this->assertSame(3, $userCart['total_count']);
    }

    public function testUserCartAndOrderLifecycle(): void
    {
        // Checkout on empty cart fails
        $emptyCheckout = $this->orderService->checkout(1);
        $this->assertFalse($emptyCheckout['success']);

        // Add items for user #1
        $this->cartService->addToCart(1, 1, 1);
        $this->cartService->addToCart(1, 1, 1); // increments to 2
        $this->cartService->addToCart(1, 2, 1);

        // Update & remove item
        $this->cartService->updateQuantity(1, 2, 2);
        $this->cartService->removeFromCart(1, 2);

        $cart = $this->cartService->getCartDetails(1);
        $this->assertCount(1, $cart['items']);
        $this->assertEquals(25.00, $cart['total_price']);

        // Place order via checkout
        $checkoutRes = $this->orderService->checkout(1);
        $this->assertTrue($checkoutRes['success']);
        $orderId = $checkoutRes['order_id'];

        // Cart should now be empty
        $this->assertCount(0, $this->cartService->getCartDetails(1)['items']);

        // Fetch user orders
        $userOrders = $this->orderService->getUserOrders(1);
        $this->assertCount(1, $userOrders);
        $this->assertEquals(25.00, (float)$userOrders[0]['total_price']);
        $this->assertSame('PENDING', $userOrders[0]['status']);

        // Admin order operations & Dashboard stats
        $adminOrderCtrl = new AdminOrderController();
        $allOrders = $adminOrderCtrl->getAllOrdersForAdmin('PENDING');
        $this->assertCount(1, $allOrders);

        // Update status to COMPLETED
        $this->assertFalse($this->orderService->updateOrderStatus($orderId, 'INVALID_STATUS')['success']);
        $statusUpd = $this->orderService->updateOrderStatus($orderId, 'COMPLETED');
        $this->assertTrue($statusUpd['success']);

        // Cannot cancel a COMPLETED order
        $cancelFail = $this->orderService->cancelOrder(1, $orderId);
        $this->assertFalse($cancelFail['success']);

        // Check dashboard revenue reflects COMPLETED order
        $stats = $adminOrderCtrl->getDashboardStats();
        $this->assertEquals(25.00, $stats['total_revenue']);
        $this->assertSame(1, $stats['total_orders']);

        // Create a second order and cancel it while PENDING
        $this->cartService->addToCart(1, 13, 1);
        $order2 = $this->orderService->checkout(1);
        $cancelOk = $this->orderService->cancelOrder(1, $order2['order_id']);
        $this->assertTrue($cancelOk['success']);

        // Delete order
        $delOk = $this->orderService->deleteOrder($order2['order_id']);
        $this->assertTrue($delOk['success']);
    }

    public function testMomoPaymentGatewayLifecycle(): void
    {
        $momoService = new MomoService();

        // USD to VND conversion
        $this->assertSame(312500, $momoService->convertUsdToVnd(12.50));
        $this->assertSame('312,500 VND', $momoService->formatVnd(312500));

        // Add item and checkout with MOMO
        $this->cartService->addToCart(1, 1, 2); // $25.00
        $checkoutRes = $this->orderService->checkout(1, 'MOMO');
        $this->assertTrue($checkoutRes['success']);
        $this->assertSame('MOMO', $checkoutRes['payment_method']);
        $orderId = (int)$checkoutRes['order_id'];

        // Create MoMo payment intent
        $intent = $momoService->createPaymentIntent(1, $orderId);
        $this->assertTrue($intent['success']);
        $this->assertSame(625000, $intent['amount_vnd']);
        $this->assertNotEmpty($intent['request_signature']);
        $this->assertNotEmpty($intent['success_signature']);

        // Invalid signature callback should fail
        $badCallback = $momoService->handleCallback(1, [
            'internal_order_id' => $orderId,
            'orderId' => $intent['momo_order_id'],
            'amount' => $intent['amount_vnd'],
            'resultCode' => 0,
            'signature' => 'invalid_hmac'
        ]);
        $this->assertFalse($badCallback['success']);

        // Cancelled payment callback (resultCode = 1006)
        $cancelCallback = $momoService->handleCallback(1, [
            'internal_order_id' => $orderId,
            'orderId' => $intent['momo_order_id'],
            'amount' => $intent['amount_vnd'],
            'resultCode' => 1006,
            'signature' => $intent['cancel_signature']
        ]);
        $this->assertFalse($cancelCallback['success']);

        // Successful payment callback (resultCode = 0)
        $okCallback = $momoService->handleCallback(1, [
            'internal_order_id' => $orderId,
            'orderId' => $intent['momo_order_id'],
            'amount' => $intent['amount_vnd'],
            'resultCode' => 0,
            'transId' => 'MOMO987654321',
            'signature' => $intent['success_signature']
        ]);
        $this->assertTrue($okCallback['success']);

        // Cannot create payment intent again for an already PAID order
        $paidIntent = $momoService->createPaymentIntent(1, $orderId);
        $this->assertFalse($paidIntent['success']);
    }
}
