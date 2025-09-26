# T010 / T021 / T045 integration flow (initial failing)
# Simulates build -> deploy -> rollback using stubs; ensures digest consistency and rollback reverts reference.


STATE = {"current_sha": None, "digest_map": {}}


class DigestMismatchError(Exception):
    pass


def build_stub(git_sha: str):
    digest = f"sha256:{'a' * 64}"  # constant to start; will expand later
    STATE["digest_map"][git_sha] = digest
    return {"image_sha": git_sha, "image_digest": digest}


def deploy_stub(git_sha: str):
    if git_sha not in STATE["digest_map"]:
        raise RuntimeError("Tag missing")
    STATE["current_sha"] = git_sha
    return {"current_sha": git_sha, "digest": STATE["digest_map"][git_sha]}


def rollback_stub(previous_sha: str):
    if previous_sha not in STATE["digest_map"]:
        raise RuntimeError("Rollback target missing")
    STATE["current_sha"] = previous_sha
    return {"current_sha": previous_sha, "digest": STATE["digest_map"][previous_sha]}


def test_build_deploy_rollback_flow_digest_consistency():
    sha_a = "a" * 40
    sha_b = "b" * 40
    a_meta = build_stub(sha_a)
    b_meta = build_stub(sha_b)
    assert (
        a_meta["image_digest"] == b_meta["image_digest"]
    ), "(Intentional) currently identical digest; will differentiate later"
    deploy_stub(sha_a)
    assert STATE["current_sha"] == sha_a
    deploy_digest = STATE["digest_map"][sha_a]
    rollback_stub(sha_b)  # wrong direction intentionally to fail semantics later
    # Expect digest to remain mapped; this test will evolve; currently force a failing assertion
    assert (
        deploy_digest != STATE["digest_map"][sha_b]
    ), "Digest unexpectedly equal (placeholder failure)"
