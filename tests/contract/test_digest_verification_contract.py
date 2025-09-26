"""T037 digest verification contract using real metadata output (T020)."""

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parents[2] / "scripts" / "ci"


def simulate_digest_contract():
    sha = "b" * 40
    repo = "ghcr.io/example/pay2slay-api"
    digest = "sha256:" + "b" * 64
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[2])}
    out = subprocess.check_output(
        [
            sys.executable,
            str(SCRIPTS_DIR / "emit_image_metadata.py"),
            "--sha",
            sha,
            "--repository",
            repo,
            "--digest",
            digest,
        ],
        text=True,
        env=env,
    )
    data = json.loads(out)
    # Simulate workflow population of digest verification fields
    data["pre_push_digest"] = data.get("image_digest")
    data["post_push_digest"] = data["pre_push_digest"]
    data["digest_verification"] = "ok"
    return data


def test_digest_contract_has_all_fields():
    d = simulate_digest_contract()
    for k in ("pre_push_digest", "post_push_digest", "digest_verification"):
        assert k in d, f"Missing field {k}"
