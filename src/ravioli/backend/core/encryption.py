"""
Encryption utilities for sensitive configuration values.
Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
"""
from cryptography.fernet import Fernet, InvalidToken
from ravioli.backend.core.config import settings


def _get_fernet() -> Fernet:
    return Fernet(settings.secret_key.encode())


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string and return a base64-encoded ciphertext string."""
    if not plaintext:
        return ""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string back to plaintext. Returns empty string on failure."""
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        return ""
