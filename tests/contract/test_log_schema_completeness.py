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
    # Missing several fields intentionally
    return {"image_sha": "a" * 40, "repository": "ghcr.io/mconstant/pay2slay-api"}


def test_log_schema_complete():
    log = generate_log_stub()
    missing = REQUIRED - set(log)
    assert not missing, f"Missing fields: {missing}"
