# T009 signature soft verification contract test (initial failing)


def soft_verify_stub(has_signature: bool):
    if has_signature:
        return {"signature_status": "verified", "signature_reason": "n/a"}
    # Missing signature path (non-fatal) - intentionally omit reason key to fail test initially
    return {"signature_status": "unverified"}


def test_signature_soft_verify_includes_reason():
    data = soft_verify_stub(False)
    assert "signature_reason" in data, "signature_reason missing for unverified signature"
    assert data.get("signature_status") in {"verified", "unverified"}
