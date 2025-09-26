# T039 rollback no-build side effect test (initial failing)


class BuildSentinel:
    called = False


def forbidden_build():
    BuildSentinel.called = True


def rollback_stub(previous_sha: str, target_sha: str):
    # Intentionally call forbidden_build to force failure
    forbidden_build()
    return {"previous_sha": previous_sha, "image_sha": target_sha}


def test_rollback_no_build_side_effect():
    BuildSentinel.called = False
    rollback_stub("a" * 40, "b" * 40)
    assert BuildSentinel.called is False, "Rollback invoked a build function (should be prohibited)"
