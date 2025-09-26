# T037 adjunct digest verification contract (initial failing)


def simulate_digest_contract():
    return {
        "pre_push_digest": "sha256:" + "a" * 64
    }  # missing post_push_digest & digest_verification


def test_digest_contract_has_all_fields():
    d = simulate_digest_contract()
    for k in ("pre_push_digest", "post_push_digest", "digest_verification"):
        assert k in d, f"Missing field {k}"
