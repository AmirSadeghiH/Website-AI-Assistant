"""Encrypted-at-rest model fields for sensitive provider credentials.

The encryption key is derived from Django's SECRET_KEY with PBKDF2, so no
extra environment variable is required. Rotating SECRET_KEY makes previously
stored values undecryptable; keep a backup of SECRET_KEY if you ever rotate it.
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)

_PREFIX = "enc:v1:"
_KEY_CACHE = {}
_PBKDF2_ITERATIONS = 200_000


def _fernet() -> Fernet:
    key = _KEY_CACHE.get("key")
    if key is None:
        secret = str(settings.SECRET_KEY).encode("utf-8")
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            secret,
            b"ai-support-field-encryption",
            _PBKDF2_ITERATIONS,
            dklen=32,
        )
        key = base64.urlsafe_b64encode(derived)
        _KEY_CACHE["key"] = key
    return Fernet(key)


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
        try:
            token = value[len(_PREFIX):]
            return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError) as exc:
            logger.error("Could not decrypt provider field: %s", exc)
            return ""

    def to_python(self, value):
        if value in (None, ""):
            return ""
        if not value.startswith(_PREFIX):
            return value
        try:
            token = value[len(_PREFIX):]
            return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError) as exc:
            logger.error("Could not decrypt provider field: %s", exc)
            return ""
