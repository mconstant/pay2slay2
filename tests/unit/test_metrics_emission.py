# T052 metrics emission unit test (initial failing)
from src.lib import observability as obs

EXPECTED_COUNT = 1


def test_metrics_label_increment():
    obs.record_image_build("canonical")
    value = obs.get_metric_value("image_build_total|canonical")
    assert value == EXPECTED_COUNT
