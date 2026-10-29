<?php

require_once ROOT_PATH . '/app/modules/menu/menu_model.php';

class MenuDetailService
{
    private $menuDetailModel;

    public function __construct()
    {
        $this->menuDetailModel = new MenuDetailModel();
    }

    public function getProductDetail($slug)
    {
        if (empty($slug)) {
            return null;
        }

        $product = $this->menuDetailModel->getProductBySlug($slug);

        if ($product) {
            $product['image_path'] = $this->formatImagePath(
                $product['category_slug'] ?? 'starters',
                $product['image_url']
            );
            $product['reviews'] = $this->menuDetailModel->getReviewsByProductId((int)$product['id']);
        }

        return $product;
    }

    public function submitReview(int $userId, int $productId, int $rating, string $comment): array
    {
        $comment = trim($comment);
        if ($rating < 1 || $rating > 5) {
            return ['success' => false, 'message' => 'Rating must be between 1 and 5 stars.'];
        }
        if (empty($comment)) {
            return ['success' => false, 'message' => 'Please enter your review comment.'];
        }

        $saved = $this->menuDetailModel->addReview($userId, $productId, $rating, $comment);
        if (!$saved) {
            return ['success' => false, 'message' => 'Could not submit review. Please try again.'];
        }

        return ['success' => true, 'message' => 'Thank you! Your review has been posted.'];
    }

    private function formatImagePath($category_slug, $image_name)
    {
        $category_slug = $category_slug ?: 'starters';
        return base_url("images/{$category_slug}/{$image_name}");
    }
}
