"""Encrypted-at-rest model fields for sensitive provider credentials.

The encryption key is derived from Django's SECRET_KEY with PBKDF2, so no
extra environment variable is required. Rotating SECRET_KEY makes previously
stored values undecryptable; keep a backup of SECRET_KEY if you ever rotate it.
"""

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)

_PREFIX = "enc:v1:"
_KEY_CACHE = {}
_PBKDF2_ITERATIONS = 200_000


def _encryption_secrets():
    values = [
        os.getenv("FIELD_ENCRYPTION_KEY", ""),
        os.getenv("FIELD_ENCRYPTION_KEY_FALLBACK", ""),
        str(settings.SECRET_KEY),
    ]
    return tuple(value.encode("utf-8") for value in values if value)


def _fernet_keys():
    cached = _KEY_CACHE.get("keys")
    if cached is not None:
        return cached
    keys = []
    for secret in _encryption_secrets():
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            secret,
            b"ai-support-field-encryption",
            _PBKDF2_ITERATIONS,
            dklen=32,
        )
        key = base64.urlsafe_b64encode(derived)
        if key not in keys:
            keys.append(key)
    _KEY_CACHE["keys"] = tuple(keys)
    return tuple(keys)


def _fernet() -> Fernet:
    return Fernet(_fernet_keys()[0])


class EncryptedCharField(models.CharField):
    """CharField that encrypts its value at rest.

    Stored format: ``enc:v1:<fernet-token>``. Empty strings are stored as-is
    (nothing to protect) so ``blank=True`` fields behave like normal.
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return ""
        if isinstance(value, str) and value.startswith(_PREFIX):
            return value
        token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
        return _PREFIX + token

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return ""
        if not value.startswith(_PREFIX):
            return value
        token = value[len(_PREFIX):].encode("ascii")
        for key in _fernet_keys():
            try:
                return Fernet(key).decrypt(token).decode("utf-8")
            except (InvalidToken, ValueError):
                continue
        logger.error("Could not decrypt provider field with configured keys.")
        return ""

    def to_python(self, value):
        if value in (None, ""):
            return ""
        if not value.startswith(_PREFIX):
            return value
        token = value[len(_PREFIX):].encode("ascii")
        for key in _fernet_keys():
            try:
                return Fernet(key).decrypt(token).decode("utf-8")
            except (InvalidToken, ValueError):
                continue
        logger.error("Could not decrypt provider field with configured keys.")
        return ""
