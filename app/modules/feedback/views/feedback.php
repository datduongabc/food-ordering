<?php
if (!isset($feedbacks)) {
    require_once ROOT_PATH . '/app/modules/feedback/feedback_controller.php';
    $feedback_controller = new FeedbackController();
    $feedbacks = $feedback_controller->getTopFeedback();
}
?>

<!-- Feedback -->
<section class="py-5 bg-soft-cyan" id="feedback">
    <div class="container">
        <header class="text-center mb-5">
            <h2 class="fw-bold text-teal-dark mb-1">What Did Our Customers Say?</h2>
            <p class="text-muted small mb-0">Authentic reviews from our valued diners</p>
        </header>
        <?php if (empty($feedbacks)): ?>
            <div class="card border-0 shadow-sm rounded-4 p-5 text-center bg-white mx-auto" style="max-width: 640px;">
                <i class="bi bi-chat-square-quote display-4 text-primary-orange mb-3"></i>
                <h5 class="fw-bold text-teal-dark">No Customer Reviews Yet</h5>
                <p class="text-muted small mb-0">Explore our menu and be the first to rate and review our signature dishes.</p>
            </div>
        <?php else: ?>
        <div id="feedbackCarousel" class="carousel slide" data-bs-ride="carousel">
            <div class="carousel-inner">
                <?php foreach ($feedbacks as $index => $feedback): ?>
                    <div class="carousel-item <?= $index === 0 ? 'active' : '' ?>">
                        <div class="row justify-content-center px-lg-4">
                            <div class="col-12 col-md-8 col-lg-6 feedback-col mb-3">
                                <div class="card hover-card p-4 p-lg-5 text-center shadow-sm h-100">
                                    <div>
                                        <h3 class="fw-bold fs-4 mb-2 text-teal-dark">
                                            <i class="bi bi-person-circle"></i>
                                            <?= e($feedback['user_name'] ?? 'Valued Guest'); ?>
                                        </h3>
                                    </div>
                                    <div>
                                        <span class="badge bg-soft-cyan text-teal-dark mb-3 px-3 py-2 rounded-pill">
                                            <i class="bi bi-egg-fried me-1"></i><?= e($feedback['product_name']); ?>
                                        </span>
                                        <p class="text-muted fst-italic mb-3 fs-6">
                                            "<?= e($feedback['comment']); ?>"
                                        </p>
                                    </div>
                                    <div class="d-flex justify-content-center align-items-center gap-2 mt-auto">
                                        <p class="text-primary-orange fs-4 mb-0">
                                            <?= $feedback['feedback_stars']; ?>
                                        </p>
                                        <p class="text-muted fw-bold fs-6 mb-0">
                                            (<?= number_format((float)$feedback['feedback_ratings'], 1); ?>)
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>

            <button
                class="carousel-control-prev"
                type="button"
                data-bs-target="#feedbackCarousel"
                data-bs-slide="prev">
                <span class="carousel-control-prev-icon bg-dark rounded-circle" aria-hidden="true"></span>
            </button>
            <button
                class="carousel-control-next"
                type="button"
                data-bs-target="#feedbackCarousel"
                data-bs-slide="next">
                <span class="carousel-control-next-icon bg-dark rounded-circle" aria-hidden="true"></span>
            </button>

            <div class="carousel-indicators">
                <?php foreach ($feedbacks as $index => $feedback): ?>
                    <button
                        class="<?= $index === 0 ? 'active' : '' ?>"
                        type="button"
                        data-bs-target="#feedbackCarousel"
                        data-bs-slide-to="<?= $index ?>"
                        aria-current="<?= $index === 0 ? 'true' : 'false' ?>">
                    </button>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>
    </div>
</section>
