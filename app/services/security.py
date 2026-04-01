"""
Security utility module
Data encryption, audit logging helpers
"""
import hashlib
import hmac
import logging
import base64
import os

logger = logging.getLogger(__name__)

# AES encryption key (32 bytes for AES-256)
# In production, load from environment variable
_ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '').encode()


def encrypt_data(plaintext: str) -> str:
    """Encrypt sensitive data using AES-256-CBC."""
    if not _ENCRYPTION_KEY:
        # Fallback: simple obfuscation for development
        return base64.b64encode(plaintext.encode()).decode()

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding

        key = _ENCRYPTION_KEY[:32].ljust(32, b'\0')
        iv = os.urandom(16)

        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode()) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()

        return base64.b64encode(iv + encrypted).decode()
    except ImportError:
        logger.warning("cryptography not installed, using base64 fallback")
        return base64.b64encode(plaintext.encode()).decode()


def decrypt_data(ciphertext: str) -> str:
    """Decrypt data encrypted with encrypt_data."""
    if not _ENCRYPTION_KEY:
        return base64.b64decode(ciphertext.encode()).decode()

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding

        key = _ENCRYPTION_KEY[:32].ljust(32, b'\0')
        raw = base64.b64decode(ciphertext.encode())
        iv = raw[:16]
        encrypted = raw[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(encrypted) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        return (unpadder.update(padded) + unpadder.finalize()).decode()
    except ImportError:
        return base64.b64decode(ciphertext.encode()).decode()


def verify_signature(data: str, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    expected = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def generate_signature(data: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature."""
    return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()


def mask_phone(phone: str) -> str:
    """Mask phone number for display: 138****5678"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + '****' + phone[-4:]
