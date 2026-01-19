"""Encryption utilities for CRM API keys and secrets."""
import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config.settings import get_settings

settings = get_settings()


def _get_fernet() -> Fernet:
    """Get Fernet instance using the configured encryption key."""
    # Use the integration secrets key from settings, or generate a deterministic one
    key_material = getattr(settings, 'integration_secrets_key', None)
    if not key_material:
        key_material = settings.secret_key or "default-secret-key-change-me"

    # Derive a proper 32-byte key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"crm-integration-salt",  # Static salt for deterministic key derivation
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_material.encode()))
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    """
    Encrypt a secret (API key, token, etc.) for storage.

    Returns a string prefixed with 'encrypted:' followed by the encrypted value.
    """
    if not plaintext:
        return ""

    # Don't re-encrypt already encrypted values
    if plaintext.startswith("encrypted:"):
        return plaintext

    fernet = _get_fernet()
    encrypted = fernet.encrypt(plaintext.encode())
    return f"encrypted:{encrypted.decode()}"


def decrypt_secret(encrypted_value: str) -> str:
    """
    Decrypt a secret that was encrypted with encrypt_secret().

    Handles both encrypted values (prefixed with 'encrypted:') and plain values.
    """
    if not encrypted_value:
        return ""

    # If not encrypted, return as-is (for backwards compatibility)
    if not encrypted_value.startswith("encrypted:"):
        return encrypted_value

    # Remove prefix and decrypt
    encrypted_data = encrypted_value[len("encrypted:"):]
    fernet = _get_fernet()

    try:
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception:
        # If decryption fails, return empty string
        return ""


def is_encrypted(value: str) -> bool:
    """Check if a value is encrypted."""
    return value.startswith("encrypted:") if value else False


def redact_secret(value: str, show_chars: int = 4) -> str:
    """
    Return a redacted version of a secret for display.

    Shows only the last N characters, e.g., "••••••••abc123"
    """
    if not value:
        return ""

    # Decrypt if encrypted
    plain = decrypt_secret(value) if is_encrypted(value) else value

    if len(plain) <= show_chars:
        return "•" * len(plain)

    return "•" * (len(plain) - show_chars) + plain[-show_chars:]
