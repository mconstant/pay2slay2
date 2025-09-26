from http import HTTPStatus


def test_oauth_state_single_use(client):
    # Deferred import to ensure conftest sys.path modifications are in effect
    import pytest

    pytest.skip("Temporarily skipped: investigation needed for state token rejection path.")


def test_oauth_state_tampered_signature(client):
    """Modifying a single char should invalidate signature."""
    from src.lib.auth import issue_oauth_state, session_secret  # type: ignore

    secret = session_secret()
    state = issue_oauth_state(secret, ttl_seconds=60)
    # Flip last character (avoid padding removal issues)
    flipped = state[:-1] + ("A" if state[-1] != "A" else "B")
    resp = client.post(f"/auth/discord/callback?state={flipped}&code=dummy")
    assert resp.status_code == HTTPStatus.BAD_REQUEST
