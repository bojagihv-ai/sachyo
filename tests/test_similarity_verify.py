from src.core.models import ListingCandidate, ListingMeta, SimilarityResult
from src.core.similarity import classify_similarity
from src.core.verify import verify_candidate


def test_classification_class1():
    s = SimilarityResult(phash_distance=3, ssim=0.95, embedding_similarity=0.97, color_similarity=0.8, text_similarity=0.4)
    classify_similarity(s)
    assert s.class_label == "class_1_same_photo"
    assert s.score >= 90


def test_verify_returns_structure():
    c = ListingCandidate(platform="coupang", item_id="x", url="https://example.com", title="브랜드 모델 500ml")
    m = ListingMeta(price_min=19900, category="생활")
    s = SimilarityResult(class_label="class_2_same_product_diff_photo", score=82)
    v = verify_candidate("브랜드 모델 500ml", c, m, s)
    assert isinstance(v.verified_flag, bool)
    assert "1_image_similarity" in v.checklist
