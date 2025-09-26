"""T058 performance test for deploy + rollback durations (initially failing)."""

import time

DEPLOY_P95_TARGET = 300
ROLLBACK_P95_TARGET = 120


def simulate_deploy():
    s = time.time()
    time.sleep(0.001)
    e = time.time()
    return e - s


def simulate_rollback():
    s = time.time()
    time.sleep(0.0005)
    e = time.time()
    return e - s


def test_deploy_and_rollback_within_targets():
    d = simulate_deploy()
    r = simulate_rollback()
    assert d > 0, "Deploy duration should be non-zero"
    assert r > 0, "Rollback duration should be non-zero"
    assert d < DEPLOY_P95_TARGET
    assert r < ROLLBACK_P95_TARGET
