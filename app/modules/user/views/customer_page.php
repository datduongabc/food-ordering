<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DaTeNO Restaurant - Fine Dining & Online Ordering</title>
    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <!-- Custom -->
    <link rel="stylesheet" href="<?= base_url('css/style.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/header.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/best_seller.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/menu_list.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/feedback.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/reservation.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/footer.css') ?>">
    <!-- Search, sort, cart, reservation -->
    <script src="<?= base_url('js/reservation/reservation.js') ?>" defer></script>
    <script src="<?= base_url('js/header/search.js') ?>" defer></script>
    <script src="<?= base_url('js/menu/sort.js') ?>" defer></script>
    <script src="<?= base_url('js/cart/cart.js') ?>" defer></script>
</head>

<body>
    <?php include ROOT_PATH . '/app/core/views/layouts/header.php'; ?>

    <main>
        <?php
        include ROOT_PATH . '/app/modules/product/views/best_seller.php';
        include ROOT_PATH . '/app/modules/product/views/menu_title.php';
        include ROOT_PATH . '/app/modules/feedback/views/feedback.php';
        include ROOT_PATH . '/app/modules/reservation/views/reservation.php';
        ?>
    </main>

    <?php include ROOT_PATH . '/app/core/views/layouts/footer.php'; ?>
</body>

</html>
