"""Integration flow test (T010 evolved for T021, T045).

Simulates build -> deploy (to B) -> rollback to A ensuring:
 - Digests remain stable per SHA
 - Rollback sets current_sha to previous release
 - No rebuild is performed (simulated via digest map unchanged)
"""

STATE = {"current_sha": None, "digest_map": {}, "build_count": 0}


class DigestMismatchError(Exception):
    pass


def build_stub(git_sha: str):
    # Derive deterministic digest from sha prefix (stable) to show difference
    digest = f"sha256:{git_sha[0] * 64}"
    STATE["digest_map"][git_sha] = digest
    STATE["build_count"] += 1
    return {"image_sha": git_sha, "image_digest": digest}


def deploy_stub(git_sha: str):
    if git_sha not in STATE["digest_map"]:
        raise RuntimeError("Tag missing")
    STATE["current_sha"] = git_sha
    return {"current_sha": git_sha, "digest": STATE["digest_map"][git_sha]}


def rollback_stub(target_previous_sha: str):
    if target_previous_sha not in STATE["digest_map"]:
        raise RuntimeError("Rollback target missing")
    # No new build; just switch reference
    STATE["current_sha"] = target_previous_sha
    return {"current_sha": target_previous_sha, "digest": STATE["digest_map"][target_previous_sha]}


def test_build_deploy_rollback_flow_digest_consistency():
    sha_a = "a" * 40  # initial prod
    sha_b = "b" * 40  # new release
    a_meta = build_stub(sha_a)
    b_meta = build_stub(sha_b)
    assert a_meta["image_digest"] != b_meta["image_digest"], "Digests should differ across SHAs"
    deploy_stub(sha_b)
    assert STATE["current_sha"] == sha_b
    deploy_digest = STATE["digest_map"][sha_b]
    builds_before = STATE["build_count"]
    rb = rollback_stub(sha_a)
    assert rb["current_sha"] == sha_a, "Rollback did not switch current_sha"
    assert STATE["digest_map"][sha_a] == a_meta["image_digest"], "Rollback altered digest mapping"
    assert deploy_digest == STATE["digest_map"][sha_b], "Deploy digest changed after rollback"
    assert STATE["build_count"] == builds_before, "Rollback triggered an unexpected build"
