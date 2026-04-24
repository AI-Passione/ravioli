import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock
from cryptography.fernet import Fernet

# Generate a deterministic test key
_TEST_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def patch_secret_key(mocker):
    """Override the SECRET_KEY so encryption tests are self-contained."""
    mocker.patch(
        "ravioli.backend.core.encryption.settings",
        secret_key=_TEST_KEY,
    )


# ── Encryption utility tests ─────────────────────────────────────────────────

def test_encrypt_and_decrypt_roundtrip(mocker):
    from ravioli.backend.core.encryption import encrypt_value, decrypt_value
    plaintext = "sk-super-secret-api-key"
    ciphertext = encrypt_value(plaintext)
    assert ciphertext != plaintext
    assert decrypt_value(ciphertext) == plaintext


def test_encrypt_empty_string_returns_empty(mocker):
    from ravioli.backend.core.encryption import encrypt_value
    assert encrypt_value("") == ""


def test_decrypt_empty_string_returns_empty(mocker):
    from ravioli.backend.core.encryption import decrypt_value
    assert decrypt_value("") == ""


def test_decrypt_invalid_token_returns_empty(mocker):
    from ravioli.backend.core.encryption import decrypt_value
    assert decrypt_value("not-valid-ciphertext") == ""


# ── Settings endpoint tests ───────────────────────────────────────────────────

def _make_mock_setting(key="ollama", value=None):
    s = MagicMock()
    s.key = key
    s.value = value or {"mode": "default", "base_url": "http://localhost:11434", "api_key": ""}
    s.updated_at = datetime.now(UTC)
    return s


def test_get_setting_not_found(client, session):
    session.query.return_value.filter.return_value.first.return_value = None
    response = client.get("/api/v1/settings/ollama")
    assert response.status_code == 404
    assert response.json()["detail"] == "Setting not found"


def test_get_setting_returns_redacted_api_key(client, session, mocker):
    mocker.patch("ravioli.backend.core.encryption.settings", secret_key=_TEST_KEY)
    from ravioli.backend.core.encryption import encrypt_value
    encrypted = encrypt_value("my-secret-key")
    mock_setting = _make_mock_setting(value={
        "mode": "cloud", "api_key": encrypted, "default_model": "gemma3:4b"
    })
    session.query.return_value.filter.return_value.first.return_value = mock_setting

    response = client.get("/api/v1/settings/ollama")
    assert response.status_code == 200
    data = response.json()
    # api_key must be redacted, never the actual value
    assert data["value"]["api_key"] == "••••••••"


def test_get_setting_empty_api_key_not_redacted(client, session):
    mock_setting = _make_mock_setting(value={"mode": "default", "api_key": ""})
    session.query.return_value.filter.return_value.first.return_value = mock_setting
    response = client.get("/api/v1/settings/ollama")
    assert response.status_code == 200
    # Empty key should not be replaced with the redacted placeholder
    assert response.json()["value"]["api_key"] == ""


def test_put_setting_creates_new(client, session, mocker):
    mocker.patch("ravioli.backend.core.encryption.settings", secret_key=_TEST_KEY)
    session.query.return_value.filter.return_value.first.return_value = None
    # refresh after commit should return the saved model
    saved = _make_mock_setting(value={"mode": "default", "api_key": ""})
    session.refresh.side_effect = lambda obj: None
    # simulate the object being returned after add+commit
    session.query.return_value.filter.return_value.first.side_effect = [None, saved]

    response = client.put("/api/v1/settings/ollama", json={
        "key": "ollama",
        "value": {"mode": "default", "api_key": ""}
    })
    assert response.status_code == 200
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_put_setting_encrypts_api_key(client, session, mocker):
    mocker.patch("ravioli.backend.core.encryption.settings", secret_key=_TEST_KEY)
    session.query.return_value.filter.return_value.first.return_value = None
    captured_value = {}

    def capture_add(obj):
        captured_value.update(obj.value)

    session.add.side_effect = capture_add
    saved = _make_mock_setting(value={"mode": "cloud", "api_key": "ENCRYPTED"})
    session.refresh.side_effect = lambda obj: None

    # Simulate: first query finds nothing (create path), refresh returns saved
    first_call = True
    def first_or_none():
        nonlocal first_call
        if first_call:
            first_call = False
            return None
        return saved
    session.query.return_value.filter.return_value.first.side_effect = first_or_none

    client.put("/api/v1/settings/ollama", json={
        "key": "ollama",
        "value": {"mode": "cloud", "api_key": "plaintext-secret"}
    })

    # The captured value should NOT be the plaintext
    assert captured_value.get("api_key") != "plaintext-secret"
    assert captured_value.get("api_key") != ""


def test_put_setting_preserves_existing_key_when_redacted(client, session, mocker):
    mocker.patch("ravioli.backend.core.encryption.settings", secret_key=_TEST_KEY)
    from ravioli.backend.core.encryption import encrypt_value
    existing_encrypted = encrypt_value("original-key")
    existing = _make_mock_setting(value={"mode": "cloud", "api_key": existing_encrypted})
    session.query.return_value.filter.return_value.first.return_value = existing
    session.refresh.side_effect = lambda obj: None

    client.put("/api/v1/settings/ollama", json={
        "key": "ollama",
        "value": {"mode": "cloud", "api_key": "••••••••"}
    })
    # The existing encrypted value must not have been overwritten
    assert existing.value["api_key"] == existing_encrypted


def test_put_setting_key_mismatch_returns_400(client, session):
    response = client.put("/api/v1/settings/ollama", json={
        "key": "different_key",
        "value": {"mode": "default"}
    })
    assert response.status_code == 400
