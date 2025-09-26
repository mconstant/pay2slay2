# T011 performance smoke test (initial failing)
import time

BUDGET_SECONDS = 600


def simulate_build_operation():
    # Placeholder: no real work; just zero duration
    start = time.time()
    end = start  # zero
    return end - start


def test_build_duration_under_budget():
    duration = simulate_build_operation()
    assert (
        duration > 0
    ), "Placeholder should be adjusted to simulate real duration (forcing failure)"
    assert duration < BUDGET_SECONDS
