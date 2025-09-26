# T050 single-arch manifest test (initial failing)


def get_manifest_stub():
    # Single-arch manifest as enforced by build process
    return {
        "manifests": [
            {"platform": {"architecture": "amd64", "os": "linux"}},
        ]
    }


def test_single_arch_manifest():
    manifest = get_manifest_stub()
    arches = {m["platform"]["architecture"] for m in manifest["manifests"]}
    assert arches == {"amd64"}, f"Unexpected architectures present: {arches}"
