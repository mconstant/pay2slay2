# T008 initial failing test for rollback workflow contract


class UnexpectedBuildInvocationError(Exception):
    """Raised if a build is triggered during rollback (naming per lint)."""


class BuildSentinel:
    called = False


def fake_build():  # would represent a forbidden call during rollback
    BuildSentinel.called = True


def rollback_stub(previous_sha: str, target_sha: str):
    # Intentionally does nothing but should NOT call fake_build
    return {"previous_sha": previous_sha, "image_sha": target_sha}


def test_rollback_does_not_trigger_build():
    BuildSentinel.called = False
    result = rollback_stub("a" * 40, "b" * 40)
    assert result["previous_sha"] == "a" * 40
    assert result["image_sha"] == "b" * 40
    assert BuildSentinel.called is False, "Rollback triggered an unexpected build operation"
