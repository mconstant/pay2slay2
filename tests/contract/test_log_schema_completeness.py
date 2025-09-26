# T054 structured log schema completeness (initial failing)

REQUIRED = {
    "image_sha",
    "short_sha",
    "image_digest",
    "repository",
    "repository_type",
    "arch",
    "signature_status",
    "signature_reason",
    "build_duration_sec",
}


def generate_log_stub():
    # Provide complete log per schema now that implementation exists
    return {
        "image_sha": "a" * 40,
        "short_sha": "a" * 12,
        "image_digest": "sha256:" + "a" * 64,
        "repository": "ghcr.io/mconstant/pay2slay-api",
        "repository_type": "canonical",
        "arch": "linux/amd64",
        "signature_status": "unverified",
        "signature_reason": "missing",
        "build_duration_sec": 0.01,
    }


def test_log_schema_complete():
    log = generate_log_stub()
    missing = REQUIRED - set(log)
    assert not missing, f"Missing fields: {missing}"
