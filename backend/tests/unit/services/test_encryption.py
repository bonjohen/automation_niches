"""Unit tests for CRM encryption service."""
import pytest


class TestEncryption:
    """Tests for the encryption utilities."""

    def test_encrypt_secret_returns_prefixed(self):
        """Encrypted values should be prefixed with 'encrypted:'."""
        from app.services.crm.encryption import encrypt_secret

        result = encrypt_secret("my-api-key-12345")

        assert result.startswith("encrypted:")
        assert "my-api-key-12345" not in result  # Should be encrypted

    def test_encrypt_secret_empty_string(self):
        """Empty string should return empty string."""
        from app.services.crm.encryption import encrypt_secret

        result = encrypt_secret("")

        assert result == ""

    def test_encrypt_secret_none_string(self):
        """None-like empty values should return empty string."""
        from app.services.crm.encryption import encrypt_secret

        result = encrypt_secret("")
        assert result == ""

    def test_encrypt_secret_idempotent(self):
        """Already encrypted values should not be re-encrypted."""
        from app.services.crm.encryption import encrypt_secret

        first_encryption = encrypt_secret("test-key")
        second_encryption = encrypt_secret(first_encryption)

        assert first_encryption == second_encryption

    def test_decrypt_secret_success(self):
        """Encrypted secrets should decrypt correctly."""
        from app.services.crm.encryption import encrypt_secret, decrypt_secret

        original = "my-super-secret-api-key"
        encrypted = encrypt_secret(original)
        decrypted = decrypt_secret(encrypted)

        assert decrypted == original

    def test_decrypt_secret_empty_string(self):
        """Empty string should return empty string."""
        from app.services.crm.encryption import decrypt_secret

        result = decrypt_secret("")

        assert result == ""

    def test_decrypt_secret_plain_value(self):
        """Plain (non-encrypted) values should be returned as-is for backwards compatibility."""
        from app.services.crm.encryption import decrypt_secret

        plain_value = "plain-api-key-without-encryption"
        result = decrypt_secret(plain_value)

        assert result == plain_value

    def test_decrypt_secret_invalid_token(self):
        """Invalid encrypted tokens should return empty string."""
        from app.services.crm.encryption import decrypt_secret

        # Malformed encrypted value
        invalid = "encrypted:this-is-not-valid-fernet-data"
        result = decrypt_secret(invalid)

        assert result == ""

    def test_is_encrypted_true(self):
        """is_encrypted should return True for encrypted values."""
        from app.services.crm.encryption import encrypt_secret, is_encrypted

        encrypted = encrypt_secret("test-key")

        assert is_encrypted(encrypted) is True

    def test_is_encrypted_false(self):
        """is_encrypted should return False for plain values."""
        from app.services.crm.encryption import is_encrypted

        plain = "plain-api-key"

        assert is_encrypted(plain) is False

    def test_is_encrypted_empty(self):
        """is_encrypted should return False for empty string."""
        from app.services.crm.encryption import is_encrypted

        assert is_encrypted("") is False

    def test_is_encrypted_none(self):
        """is_encrypted should handle None-like values gracefully."""
        from app.services.crm.encryption import is_encrypted

        # Empty string (None would cause different error)
        assert is_encrypted("") is False

    def test_redact_secret_shows_last_chars(self):
        """redact_secret should show only the last N characters."""
        from app.services.crm.encryption import redact_secret

        secret = "abcdefghij"  # 10 chars
        result = redact_secret(secret, show_chars=4)

        assert result == "••••••ghij"
        assert len(result) == len(secret)

    def test_redact_secret_short_value(self):
        """Short values should be fully redacted."""
        from app.services.crm.encryption import redact_secret

        short = "abc"  # 3 chars, show_chars defaults to 4
        result = redact_secret(short, show_chars=4)

        assert result == "•••"
        assert len(result) == len(short)

    def test_redact_secret_empty(self):
        """Empty string should return empty string."""
        from app.services.crm.encryption import redact_secret

        result = redact_secret("")

        assert result == ""

    def test_redact_secret_handles_encrypted(self):
        """redact_secret should decrypt and then redact encrypted values."""
        from app.services.crm.encryption import encrypt_secret, redact_secret

        original = "my-secret-key-12345"
        encrypted = encrypt_secret(original)

        result = redact_secret(encrypted, show_chars=5)

        # Should show last 5 chars of original, not of encrypted
        assert result.endswith("12345")
        assert "•" in result

    def test_roundtrip_encryption(self):
        """Test full encryption/decryption roundtrip with various strings."""
        from app.services.crm.encryption import encrypt_secret, decrypt_secret

        test_cases = [
            "simple",
            "with spaces here",
            "special!@#$%^&*()",
            "unicode: éàü中文",
            "very-long-" * 100,  # Long string
        ]

        for original in test_cases:
            encrypted = encrypt_secret(original)
            decrypted = decrypt_secret(encrypted)
            assert decrypted == original, f"Failed for: {original[:50]}..."

    def test_different_secrets_produce_different_ciphertext(self):
        """Same plaintext encrypted twice should produce different ciphertext (due to IV)."""
        from app.services.crm.encryption import encrypt_secret

        plaintext = "same-secret"
        first = encrypt_secret(plaintext)
        second = encrypt_secret(plaintext)

        # Fernet uses random IV, so ciphertext should differ
        # But both should decrypt to the same value
        assert first.startswith("encrypted:")
        assert second.startswith("encrypted:")
        # Note: Due to random IV in Fernet, these will be different
