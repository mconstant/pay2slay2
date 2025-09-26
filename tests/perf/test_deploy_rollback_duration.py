"""T058 performance test for deploy + rollback durations (initially failing)."""

import time

DEPLOY_P95_TARGET = 300
ROLLBACK_P95_TARGET = 120


def simulate_deploy():
    s = time.time()
    e = s
    return e - s


def simulate_rollback():
    s = time.time()
    e = s
    return e - s


def test_deploy_and_rollback_within_targets():
    d = simulate_deploy()
    r = simulate_rollback()
    assert d > 0, "Deploy duration placeholder must be set >0 to activate test"
    assert r > 0, "Rollback duration placeholder must be set >0 to activate test"
    assert d < DEPLOY_P95_TARGET
    assert r < ROLLBACK_P95_TARGET
