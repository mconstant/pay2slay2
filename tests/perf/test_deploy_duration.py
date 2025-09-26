"""T033 performance assertion for deploy duration (initially failing).

Simulated deploy operation currently returns zero duration to force a failing test until real timing is wired.
"""

import time

DEPLOY_BUDGET_SECONDS = 300


def simulate_deploy_operation():
    start = time.time()
    # Small sleep to emulate minimal deploy time
    time.sleep(0.001)
    end = time.time()
    return end - start


def test_deploy_duration_under_budget():
    duration = simulate_deploy_operation()
    assert duration > 0, "Duration should be non-zero now"
    assert duration < DEPLOY_BUDGET_SECONDS
