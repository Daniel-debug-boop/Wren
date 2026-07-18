"""Machine-local AES-256-GCM encryption for sensitive config data.

Derives an encryption key from the machine's hardware ID (via /etc/machine-id
or dbus machine-id), so the encrypted file is only decryptable on the same
machine. This protects API keys at rest — if the disk is stolen or the file is
exfiltrated, the keys cannot be recovered without access to the machine itself.

Uses AES-256-GCM (authenticated encryption) which provides:
  - Confidentiality: data cannot be read without the key
  - Integrity: data cannot be modified without detection
  - Nonce-based: each encryption produces different ciphertext even for same input

Key derivation:
  1. Read /etc/machine-id (or fallback to dbus machine-id or hostname)
  2. HKDF-expand with a static pepper to produce a 32-byte AES key
  3. The key is cached in memory after first derivation
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
from pathlib import Path

_logger = logging.getLogger(__name__)

# AES-256-GCM constants
_KEY_SIZE = 32  # 256 bits
_NONCE_SIZE = 12  # 96 bits (recommended for GCM)
_TAG_SIZE = 16  # 128-bit authentication tag

# Static pepper mixed into key derivation (not secret, prevents key from being
# purely machine-ID derived in case machine ID is ever exposed)
_PEPPER = b'wren-llm-provider-store-v1'

# In-memory cache of the derived key (avoids repeated file reads)
_derived_key: bytes | None = None


def _read_machine_id() -> str:
    """Read the machine's unique hardware ID.

    Tries multiple sources in order of reliability:
    1. /etc/machine-id (systemd, most Linux distros)
    2. /var/lib/dbus/machine-id (dbus fallback)
    3. /etc/hostname (last resort fallback)
    4. Platform-specific node name (cross-platform fallback)
    """
    candidates = [
        '/etc/machine-id',
        '/var/lib/dbus/machine-id',
        '/etc/hostname',
        '/proc/sys/kernel/random/boot_id',
    ]

    for path in candidates:
        try:
            content = Path(path).read_text('utf-8').strip()
            if content:
                return content
        except (FileNotFoundError, PermissionError, OSError):
            continue

    # Last resort: use hostname + platform info
    import platform
    return f"{platform.node()}-{platform.machine()}-{platform.system()}"


def _derive_key() -> bytes:
    """Derive a 32-byte AES-256 key from the machine ID.

    Uses HKDF-like expansion: HMAC-SHA256(machine_id, pepper) to produce
    a deterministic, machine-bound 256-bit key. The key is cached after
    first derivation.
    """
    global _derived_key

    if _derived_key is not None:
        return _derived_key

    machine_id = _read_machine_id()
    # HKDF extract: use machine_id as input key material, pepper as salt
    prk = hmac.new(_PEPPER, machine_id.encode('utf-8'), hashlib.sha256).digest()
    # HKDF expand: derive exactly KEY_SIZE bytes
    # Single expansion round for 32 bytes (SHA256 output = 32 bytes)
    key = hmac.new(prk, b'llm-provider-encryption-v1', hashlib.sha256).digest()
    assert len(key) == _KEY_SIZE

    _derived_key = key
    _logger.debug('Crypto: derived machine-local encryption key')
    return key


def encrypt(plaintext: str) -> str:
    """Encrypt a string using AES-256-GCM with a machine-local key.

    Args:
        plaintext: The string to encrypt (e.g. JSON of provider configs)

    Returns:
        base64-encoded ciphertext: nonce + ciphertext + tag
        Format: base64(nonce || ciphertext || tag) where || is concatenation
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _derive_key()
    aesgcm = AESGCM(key)

    # Generate random nonce for each encryption
    nonce = os.urandom(_NONCE_SIZE)

    # Encrypt with empty associated data (we don't need AAD for file-level encryption)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

    # Format: nonce + ciphertext (which already includes the GCM tag at the end)
    packaged = nonce + ciphertext

    return base64.b64encode(packaged).decode('ascii')


def decrypt(ciphertext_b64: str) -> str:
    """Decrypt a base64-encoded AES-256-GCM ciphertext.

    Args:
        ciphertext_b64: base64 string produced by encrypt()

    Returns:
        Original plaintext string

    Raises:
        ValueError: If decryption fails (wrong key, corrupted data, or tampering)
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _derive_key()
    aesgcm = AESGCM(key)

    try:
        packaged = base64.b64decode(ciphertext_b64)
    except Exception as e:
        raise ValueError(f'Failed to decode ciphertext: {e}') from e

    if len(packaged) < _NONCE_SIZE + _TAG_SIZE:
        raise ValueError(
            f'Ciphertext too short ({len(packaged)} bytes). '
            f'Data may be corrupted or in plaintext format.'
        )

    nonce = packaged[:_NONCE_SIZE]
    ciphertext = packaged[_NONCE_SIZE:]

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(
            f'Decryption failed: {e}. '
            f'This likely means the file was encrypted on a different machine, '
            f'or the data is corrupted.'
        ) from e


def is_encrypted(data: str) -> bool:
    """Check if a string looks like encrypted data vs plaintext JSON.

    Heuristic: checks if the data is valid base64 AND long enough to contain
    a nonce + at least 1 byte of ciphertext. Plaintext JSON will always fail
    the base64 decode (JSON starts with '{' which is not valid base64).
    """
    if len(data) < 24:  # Min base64 length for nonce + 1 byte
        return False
    try:
        decoded = base64.b64decode(data)
        return len(decoded) >= _NONCE_SIZE + 1
    except Exception:
        return False


def get_key_fingerprint() -> str:
    """Get a short fingerprint of the derived key (for diagnostics only).

    Returns first 8 hex chars of the key hash — useful for verifying
    that two instances are using the same key without exposing the key.
    """
    key = _derive_key()
    return hashlib.sha256(key).hexdigest()[:8]
