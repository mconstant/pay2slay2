from http import HTTPStatus


def test_oauth_state_single_use(client):
    """Valid state may be used once (second attempt rejected)."""
    from src.lib.auth import issue_oauth_state, session_secret  # type: ignore

    secret = session_secret()
    state = issue_oauth_state(secret, ttl_seconds=60)
    # First call succeeds
    first = client.post(f"/auth/discord/callback?state={state}&code=dummy")
    assert first.status_code == HTTPStatus.OK, first.text
    # Replay attempt with same state now rejected
    second = client.post(f"/auth/discord/callback?state={state}&code=dummy")
    assert second.status_code == HTTPStatus.BAD_REQUEST


def test_oauth_state_mismatch(client):
    """Completely malformed / random state rejected."""
    resp = client.post("/auth/discord/callback?state=not_a_valid_state&code=dummy")
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_oauth_state_tampered_signature(client):
    """Modifying a single char should invalidate signature."""
    from src.lib.auth import issue_oauth_state, session_secret  # type: ignore

    secret = session_secret()
    state = issue_oauth_state(secret, ttl_seconds=60)
    # Flip last character (avoid padding removal issues)
    flipped = state[:-1] + ("A" if state[-1] != "A" else "B")
    resp = client.post(f"/auth/discord/callback?state={flipped}&code=dummy")
    assert resp.status_code == HTTPStatus.BAD_REQUEST
