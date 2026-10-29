<?php

require_once ROOT_PATH . '/app/modules/cart/cart_model.php';

class CartService
{
    private $cartModel;

    public function __construct()
    {
        $this->cartModel = new CartModel();
    }

    private function formatImagePath($categorySlug, $imageName): string
    {
        $categorySlug = $categorySlug ?: 'starters';
        return base_url("images/{$categorySlug}/{$imageName}");
    }

    /**
     * Get detailed cart items and summary for either logged-in user or guest session
     */
    public function getCartDetails(?int $userId): array
    {
        $items = [];

        if ($userId) {
            $items = $this->cartModel->getUserCartItems($userId);
        } else {
            $guestCart = $_SESSION['guest_cart'] ?? [];
            if (!empty($guestCart)) {
                $products = $this->cartModel->getProductsByIds(array_keys($guestCart));
                foreach ($products as $prod) {
                    $pid = (int)$prod['product_id'];
                    if (isset($guestCart[$pid])) {
                        $prod['quantity'] = (int)$guestCart[$pid];
                        $items[] = $prod;
                    }
                }
            }
        }

        $totalPrice = 0.0;
        $totalCount = 0;

        foreach ($items as &$item) {
            $item['quantity'] = (int)$item['quantity'];
            $item['price'] = (float)$item['price'];
            $item['subtotal'] = round($item['price'] * $item['quantity'], 2);
            $item['image_path'] = $this->formatImagePath($item['category_slug'] ?? 'starters', $item['image_url']);
            $totalPrice += $item['subtotal'];
            $totalCount += $item['quantity'];
        }

        return [
            'items' => $items,
            'total_price' => round($totalPrice, 2),
            'total_count' => $totalCount
        ];
    }

    public function addToCart(?int $userId, int $productId, int $quantity = 1): array
    {
        if ($productId <= 0 || $quantity <= 0) {
            return ['success' => false, 'message' => 'Invalid product or quantity.'];
        }

        $product = $this->cartModel->findProductById($productId);
        if (!$product) {
            return ['success' => false, 'message' => 'Dish not found or unavailable.'];
        }

        $quantity = min(99, max(1, $quantity));

        if ($userId) {
            $this->cartModel->addOrIncrementItem($userId, $productId, $quantity);
            $cartCount = $this->cartModel->countUserCartItems($userId);
        } else {
            if (!isset($_SESSION['guest_cart']) || !is_array($_SESSION['guest_cart'])) {
                $_SESSION['guest_cart'] = [];
            }
            $current = (int)($_SESSION['guest_cart'][$productId] ?? 0);
            $_SESSION['guest_cart'][$productId] = min(99, $current + $quantity);
            $cartCount = (int)array_sum($_SESSION['guest_cart']);
        }

        return [
            'success' => true,
            'message' => "Added \"{$product['name']}\" to your cart!",
            'cart_count' => $cartCount,
            'product_name' => $product['name']
        ];
    }

    public function updateQuantity(?int $userId, int $productId, int $quantity): array
    {
        if ($productId <= 0) {
            return ['success' => false, 'message' => 'Invalid product.'];
        }

        if ($userId) {
            $this->cartModel->updateItemQuantity($userId, $productId, $quantity);
        } else {
            if ($quantity <= 0) {
                unset($_SESSION['guest_cart'][$productId]);
            } else {
                $_SESSION['guest_cart'][$productId] = min(99, $quantity);
            }
        }

        $details = $this->getCartDetails($userId);
        return [
            'success' => true,
            'message' => 'Cart updated.',
            'cart' => $details
        ];
    }

    public function removeFromCart(?int $userId, int $productId): array
    {
        if ($userId) {
            $this->cartModel->removeItem($userId, $productId);
        } else {
            unset($_SESSION['guest_cart'][$productId]);
        }

        return [
            'success' => true,
            'message' => 'Item removed from cart.',
            'cart' => $this->getCartDetails($userId)
        ];
    }

    public function clearCart(?int $userId): array
    {
        if ($userId) {
            $this->cartModel->clearUserCart($userId);
        } else {
            unset($_SESSION['guest_cart']);
        }

        return [
            'success' => true,
            'message' => 'Cart cleared.'
        ];
    }

    public function mergeGuestCartToUser(int $userId, array $guestCart): void
    {
        foreach ($guestCart as $productId => $qty) {
            $productId = (int)$productId;
            $qty = (int)$qty;
            if ($productId > 0 && $qty > 0) {
                $product = $this->cartModel->findProductById($productId);
                if ($product) {
                    $this->cartModel->addOrIncrementItem($userId, $productId, $qty);
                }
            }
        }
    }
}
