<?php

use PHPUnit\Framework\TestCase;

require_once ROOT_PATH . '/app/modules/product/product_controller.php';
require_once ROOT_PATH . '/app/modules/product/admin_product_controller.php';
require_once ROOT_PATH . '/app/modules/menu/menu_service.php';
require_once ROOT_PATH . '/app/modules/feedback/feedback_controller.php';

class ProductMenuFeedbackTest extends TestCase
{
    private ProductService $productService;
    private MenuDetailService $menuService;
    private FeedbackService $feedbackService;

    protected function setUp(): void
    {
        $_SESSION = [];
        TestDatabaseHelper::setup();
        $this->productService = new ProductService();
        $this->menuService = new MenuDetailService();
        $this->feedbackService = new FeedbackService();
    }

    public function testFeaturedAndPaginatedProductsAllSortModes(): void
    {
        $ctrl = new ProductController();
        $featured = $ctrl->getHighestRating();
        $this->assertNotNull($featured);
        $this->assertSame('bbq-grilled-pork-ribs', $featured['slug']);
        $this->assertStringContainsString('images/', $featured['image_path']);

        $sorts = ['default', 'price_asc', 'price_desc', 'rating_asc', 'rating_desc', 'starters', 'main_dishes'];
        foreach ($sorts as $sort) {
            $data = $ctrl->getProductsPaginated(1, 12, $sort);
            $this->assertArrayHasKey('products', $data);
            $this->assertNotEmpty($data['products']);
            $this->assertSame(1, $data['current_page']);
        }
    }

    public function testAdminProductCrudAndSoftDelete(): void
    {
        $adminCtrl = new AdminProductController();
        $categories = $adminCtrl->getCategories();
        $locations = $adminCtrl->getLocations();
        $this->assertCount(2, $categories);
        $this->assertCount(3, $locations);

        // Validation failure
        $bad = $this->productService->saveProduct(['name' => '', 'price' => 0, 'description' => '']);
        $this->assertFalse($bad['success']);

        // Create new product
        $created = $this->productService->saveProduct([
            'name' => 'Truffle Pasta',
            'category_id' => 2,
            'price' => 26.50,
            'description' => 'Fresh handmade pasta with black truffle cream.',
            'slug' => '',
            'locations' => [1, 3]
        ]);
        $this->assertTrue($created['success']);

        $allAdmin = $adminCtrl->getAllProductsForAdmin();
        $this->assertGreaterThanOrEqual(4, count($allAdmin));

        // Update existing product
        $updated = $this->productService->saveProduct([
            'name' => 'Classic Caesar Salad Deluxe',
            'category_id' => 1,
            'price' => 14.00,
            'description' => 'Updated description.',
            'slug' => 'caesar-salad',
            'locations' => [1, 2]
        ], null, 1);
        $this->assertTrue($updated['success']);

        // Toggle soft delete (hide then restore)
        $hide = $this->productService->toggleProductStatus(1);
        $this->assertTrue($hide['success']);
        $restore = $this->productService->toggleProductStatus(1);
        $this->assertTrue($restore['success']);

        // Non-existent product toggle
        $this->assertFalse($this->productService->toggleProductStatus(9999)['success']);
    }

    public function testMenuDetailAndSubmitReview(): void
    {
        $this->assertNull($this->menuService->getProductDetail(''));
        $this->assertNull($this->menuService->getProductDetail('non-existent-slug'));

        $detail = $this->menuService->getProductDetail('caesar-salad');
        $this->assertNotNull($detail);
        $this->assertSame('Classic Caesar Salad', $detail['name']);
        $this->assertNotEmpty($detail['locations']);
        $this->assertNotEmpty($detail['reviews']);

        // Invalid reviews
        $this->assertFalse($this->menuService->submitReview(1, 1, 6, 'Invalid rating')['success']);
        $this->assertFalse($this->menuService->submitReview(1, 1, 5, '   ')['success']);

        // Valid review submission updates average_rating
        $revOk = $this->menuService->submitReview(1, 1, 4, 'Very tasty and fresh!');
        $this->assertTrue($revOk['success']);

        $updatedDetail = $this->menuService->getProductDetail('caesar-salad');
        $this->assertCount(2, $updatedDetail['reviews']);
    }

    public function testFeedbackModule(): void
    {
        $feedbackCtrl = new FeedbackController();
        $feedbacks = $feedbackCtrl->getTopFeedback();
        $this->assertNotEmpty($feedbacks);
        $this->assertSame('★★★★★', $feedbacks[0]['feedback_stars']);
        $this->assertEquals(5.0, $feedbacks[0]['feedback_ratings']);
    }
}
