<?php

require_once ROOT_PATH . '/app/modules/product/product_model.php';

class ProductService
{
    private $productModel;

    public function __construct()
    {
        $this->productModel = new ProductModel();
    }

    public function getHighestRating()
    {
        $product = $this->productModel->getFeatured();
        if ($product) {
            $product['image_path'] = $this->formatImagePath($product['category_slug'], $product['image_url']);
            return $product;
        }

        return null;
    }

    public function getPaginatedData($page, $limit, $sort)
    {
        $page = max(1, (int)$page);
        $offset = ($page - 1) * $limit;

        $products = $this->productModel->getProducts($limit, $offset, $sort);
        $totalProducts = $this->productModel->countProducts($sort);

        foreach ($products as &$product) {
            $product['image_path'] = $this->formatImagePath($product['category_slug'], $product['image_url']);
        }

        return [
            'products' => $products,
            'current_page' => $page,
            'total_pages' => max(1, (int)ceil($totalProducts / $limit))
        ];
    }

    private function formatImagePath($category_slug, $image_name)
    {
        $category_slug = $category_slug ?: 'starters';
        return base_url("images/{$category_slug}/{$image_name}");
    }

    public function getProductsForAdmin()
    {
        $products = $this->productModel->getAllProductsForAdmin();
        foreach ($products as &$product) {
            $product['image_path'] = $this->formatImagePath($product['category_slug'] ?? 'starters', $product['image_url']);
            $product['location_id_array'] = !empty($product['location_ids'])
                ? array_map('intval', explode(',', $product['location_ids']))
                : [];
        }
        return $products;
    }

    public function getCategories(): array
    {
        return $this->productModel->getCategories();
    }

    public function getLocations(): array
    {
        return $this->productModel->getLocations();
    }

    private function generateSlug(string $text): string
    {
        $text = strtolower(trim($text));
        $text = preg_replace('/[^a-z0-9]+/', '-', $text);
        return trim($text, '-') ?: 'dish-' . time();
    }

    public function saveProduct(array $postData, ?array $fileData = null, ?int $productId = null): array
    {
        $name = trim($postData['name'] ?? '');
        $categoryId = (int)($postData['category_id'] ?? 1);
        $price = (float)($postData['price'] ?? 0);
        $description = trim($postData['description'] ?? '');
        $slug = trim($postData['slug'] ?? '');
        $imageUrl = trim($postData['image_url'] ?? '');
        $locationIds = isset($postData['locations']) && is_array($postData['locations'])
            ? $postData['locations']
            : [1, 2, 3];

        if (empty($name) || empty($description) || $price <= 0) {
            return ['success' => false, 'message' => 'Please provide valid dish name, price, and description.'];
        }

        if (empty($slug)) {
            $slug = $this->generateSlug($name);
        } else {
            $slug = $this->generateSlug($slug);
        }

        // Determine category slug for image folder
        $categorySlug = ($categoryId === 2) ? 'main_dishes' : 'starters';

        // Handle optional image upload
        if ($fileData && !empty($fileData['name']) && $fileData['error'] === UPLOAD_ERR_OK) {
            $ext = strtolower(pathinfo($fileData['name'], PATHINFO_EXTENSION));
            $allowed = ['webp', 'jpg', 'jpeg', 'png'];
            if (!in_array($ext, $allowed, true)) {
                return ['success' => false, 'message' => 'Only WEBP, JPG, and PNG images are allowed.'];
            }

            $fileName = str_replace('-', '_', $slug) . '.' . $ext;
            $targetDir = ROOT_PATH . "/public/images/{$categorySlug}";
            if (!is_dir($targetDir)) {
                mkdir($targetDir, 0755, true);
            }
            if (move_uploaded_file($fileData['tmp_name'], $targetDir . '/' . $fileName)) {
                $imageUrl = $fileName;
            }
        }

        if (empty($imageUrl)) {
            if ($productId) {
                $existing = $this->productModel->getProductById($productId);
                $imageUrl = $existing['image_url'] ?? 'caesar_salad.webp';
            } else {
                $imageUrl = ($categoryId === 2) ? 'beef_steak_red_wine.webp' : 'caesar_salad.webp';
            }
        }

        $payload = [
            'category_id' => $categoryId,
            'image_url' => $imageUrl,
            'name' => $name,
            'description' => $description,
            'price' => $price,
            'slug' => $slug
        ];

        if ($productId) {
            $ok = $this->productModel->updateProduct($productId, $payload, $locationIds);
            return [
                'success' => $ok,
                'message' => $ok ? "Dish \"{$name}\" updated successfully." : "Failed to update dish (slug may already exist)."
            ];
        } else {
            $ok = $this->productModel->createProduct($payload, $locationIds);
            return [
                'success' => $ok,
                'message' => $ok ? "Dish \"{$name}\" created successfully." : "Failed to create dish (slug may already exist)."
            ];
        }
    }

    public function toggleProductStatus(int $id): array
    {
        $ok = $this->productModel->toggleSoftDelete($id);
        return [
            'success' => $ok,
            'message' => $ok ? "Dish visibility status updated." : "Failed to update dish status."
        ];
    }
}
