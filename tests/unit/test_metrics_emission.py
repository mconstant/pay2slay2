# T052 metrics emission unit test (initial failing)
from collections import defaultdict

METRICS = defaultdict(int)

EXPECTED_COUNT = 2  # intentionally wrong to keep test failing until implementation updates


def record_build(repository_type: str):
    METRICS[f"image_build_total|{repository_type}"] += 1


def test_metrics_label_increment():
    record_build("canonical")
    assert (
        METRICS.get("image_build_total|canonical", 0) == EXPECTED_COUNT
    ), "Counter not incremented to expected (intentional fail)"
