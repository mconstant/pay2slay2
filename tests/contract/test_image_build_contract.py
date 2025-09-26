# T006 / T037 initial failing stub
# Expected keys per tasks: image_sha, image_digest, signature_status, signature_reason, repository,
# repository_type, short_sha, arch, build_duration_sec, pre_push_digest, post_push_digest (T037), digest_verification


def simulate_build_contract_stub():
    # Return empty to force failure until implementation
    return {}


REQUIRED_KEYS = [
    "image_sha",
    "image_digest",
    "signature_status",
    "signature_reason",
    "repository",
    "repository_type",
    "short_sha",
    "arch",
    "build_duration_sec",
]

ADDITIONAL_DIGEST_KEYS = ["pre_push_digest", "post_push_digest", "digest_verification"]


def test_image_build_contract_minimum_fields():
    data = simulate_build_contract_stub()
    missing = [k for k in REQUIRED_KEYS if k not in data]
    assert not missing, f"Missing required fields: {missing}"


def test_image_build_contract_digest_verification_fields():
    data = simulate_build_contract_stub()
    missing = [k for k in ADDITIONAL_DIGEST_KEYS if k not in data]
    assert not missing, f"Missing digest verification fields: {missing}"
