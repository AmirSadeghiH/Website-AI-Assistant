"""HMAC conversation tokens (README-promised, now actually enforced).

The widget receives a signed token together with its conversation id and
must present both when reading history or submitting feedback/leads bound
to that conversation. This prevents visitors from enumerating other
people's conversations without storing server-side sessions.
"""

import hashlib
import hmac

from django.conf import settings


def _signing_key():
    secret = settings.SECRET_KEY or "ai-support-dev"
    return hashlib.sha256(f"ai-support:conversation:{secret}".encode("utf-8")).digest()


def make_conversation_token(conversation_id):
    """Deterministic per-conversation token (no server-side storage)."""
    conversation_id = str(conversation_id)
    if not conversation_id:
        return ""
    digest = hmac.new(_signing_key(), conversation_id.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()[:40]


def verify_conversation_token(conversation_id, token):
    if not conversation_id or not token:
        return False
    expected = make_conversation_token(conversation_id)
    return hmac.compare_digest(str(token), expected)
