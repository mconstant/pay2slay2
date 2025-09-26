# T049 short tag parity (initial failing)

FAKE_REGISTRY = {}


def register_image(full_sha: str, digest: str):
    FAKE_REGISTRY[full_sha] = digest
    short = full_sha[:12]
    FAKE_REGISTRY[short] = digest


def get_digest(tag: str):
    return FAKE_REGISTRY.get(tag)


def test_short_tag_parity():
    full = "c" * 40
    digest = "sha256:" + "c" * 64
    register_image(full, digest)
    assert get_digest(full) == get_digest(full[:12])
    # Force failing expectation by mutating short tag digest
    FAKE_REGISTRY[full[:12]] = "sha256:" + "d" * 64
    assert get_digest(full) == get_digest(full[:12]), "Short tag digest diverged (placeholder fail)"
