import os
import statistics
import time
from http import HTTPStatus

import pytest

# Environment variable to allow opt-out if environment is too slow (CI flakes)
SKIP_PERF = os.getenv("PAY2SLAY_SKIP_PERF") == "1"
TARGET_P95_MS = 300
REQUESTS = 50  # modest sample for smoke test


@pytest.mark.skipif(SKIP_PERF, reason="Performance smoke tests skipped via PAY2SLAY_SKIP_PERF=1")
def test_me_status_p95_under_target(client):
    # Warm session creation (simulate registration flow minimal subset):
    client.get("/auth/discord/callback?state=xyz&code=dummy")
    client.post("/link/wallet", json={"banano_address": "ban_1exampleaddress"})

    latencies_ms: list[float] = []
    # Light warmup to ensure any lazy imports/db setup done
    for _ in range(5):
        client.get("/me/status")

    for _ in range(REQUESTS):
        start = time.perf_counter()
        resp = client.get("/me/status")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == HTTPStatus.OK
        latencies_ms.append(elapsed_ms)

    latencies_ms.sort()
    # p95 index (0-based): ceil(0.95 * n) - 1
    import math

    p95_index = max(0, math.ceil(0.95 * len(latencies_ms)) - 1)
    p95 = latencies_ms[p95_index]

    # Provide helpful diagnostic if fails
    median = statistics.median(latencies_ms)
    mean = statistics.fmean(latencies_ms)

    print(
        f"/me/status perf sample n={len(latencies_ms)} p95={p95:.2f}ms median={median:.2f}ms mean={mean:.2f}ms max={max(latencies_ms):.2f}ms"
    )

    assert (
        p95 < TARGET_P95_MS
    ), f"p95 {p95:.2f}ms exceeded target {TARGET_P95_MS}ms; stats: median={median:.2f} mean={mean:.2f} max={max(latencies_ms):.2f}"
