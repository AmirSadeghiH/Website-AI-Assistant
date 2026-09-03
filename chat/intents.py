"""Rule-based intent detection (feature #17).

Zero-cost, deterministic and safe to run on every message. The intent is
stored on messages/conversations and powers analytics, smart fallback and
lead/handoff prompts in the admin panel. Model-based classification can be
layered later without changing call sites.
"""

import re
import string

from .models import (
    INTENT_CONTACT_REQUEST,
    INTENT_GENERAL,
    INTENT_GREETING,
    INTENT_ORDER_TRACKING,
    INTENT_PRICING,
    INTENT_PURCHASE,
    INTENT_COMPLAINT,
    INTENT_SUPPORT,
    
)

# Ordered by specificity: a message matching several rules keeps the first
# (most business-critical) match.
_RULES = (
    (
        INTENT_CONTACT_REQUEST,
        (
            "تماس", "تماس بگیرید", "با من تماس", "ارتباط", "در ارتباط باش", "مشاوره",
            "گفتگو با انسان", "اپراتور", "کارشناس", "پشتیبان انسانی", "نماینده",
            "شماره تماس", "شماره شما", "آدرس", "جلسه", "دمو",
            "call me", "contact", "talk to (a )?human", "speak to (a )?(human|agent|person)",
            "phone number", "demo", "meeting",
        ),
    ),
    (
        INTENT_ORDER_TRACKING,
        (
            "پیگیری سفارش", "پیگیری درخواست", "پیگیری خرید", "کد رهگیری", "رهگیری",
            "وضعیت سفارش", "سفارشم کجاست", "سفارش من", "شماره سفارش", "ارسال شد",
            "track(ing)? (my )?order", "order status", "where is my order",
        ),
    ),
    (
        INTENT_COMPLAINT,
        (
            "شکایت", "شاکی", "ناراضی", "اعتراض", "گزارش تخلف", "ضعف", "بدکردن",
            "خیلی بد", "افتضاح", "عالی نبود", "بدترین",
            "complaint", "angry", "terrible", "awful", "unacceptable",
        ),
    ),
    (
        INTENT_PURCHASE,
        (
            "خرید", "بخرم", "می‌خرم", "میخرم", "سفارش بدهم", "ثبت سفارش", "سفارش ثبت",
            "پرداخت", "دوره را بخرم", "اشتراک", "خریداری",
            "buy", "purchase", "checkout", "place an order", "subscribe",
        ),
    ),
    (
        INTENT_PRICING,
        (
            "قیمت", "قیمتی", "هزینه", "چند است", "چنده", "چندتومان", "تومان", "تعرفه",
            "چقدر", "نرخ", "پلن", "پکیج", "رایگان",
            "price", "pricing", "cost", "how much", "fee", "rate", "plan",
        ),
    ),
    (
        INTENT_SUPPORT,
        (
            "مشکل", "خطا", "خطای", "کار نمی‌کند", "کار نمیکند", "نمی‌شود", "خراب",
            "رفع", "راهنمایی", "آموزش", "پشتیبانی", "مرجوعی", "بازپرداخت", "گارانتی",
            "سوال فنی", "همکاری نمی", "به مشکل خوردم", "ارور",
            "error", "not working", "broken", "issue", "problem", "support",
            "refund", "warranty", "return policy", "help me",
        ),
    ),
    (
        INTENT_GREETING,
        (
            "سلام", "درود", "وقت بخیر", "خوبی", "علیک",
            "^hi\\b", "^hello\\b", "^hey\\b", "good (morning|afternoon|evening)",
        ),
    ),
)

_COMPILED = tuple(
    (intent, tuple(re.compile(pattern) for pattern in patterns))
    for intent, patterns in _RULES
)

_STOPWORDS = {
    "است", "هست", "برای", "چطور", "چیست", "چیه", "میشه", "لطفا", "خواهش",
    "من", "تو", "او", "ما", "شما", "و", "به", "از", "که", "را", "با", "این",
    "آن", "یک", "درباره", "the", "a", "an", "is", "are", "of", "to", "in",
}


def _normalize(text):
    """Fold Arabic/Persian variants so matching works across keyboards."""
    return (
        str(text)
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ى", "ی")
        .replace("\u200c", " ")
        .lower()
    )


_KEY_FOLD = str.maketrans({
    "ؤ": "و",   # سؤال ↔ سوال
    "أ": "ا",
    "إ": "ا",
    "ة": "ه",
})
_ARABIC_PUNCT = "؟،؛٬٫؟"


def detect_intent(text):
    """Return the detected intent code for a visitor message.

    Uses whole-word regex matching over normalized text so that compound
    words (نمی‌کند / نمی کند) both match. Unknown input maps to ``general``.
    """
    if not text:
        return INTENT_GENERAL
    normalized = _normalize(text).strip()
    for intent, patterns in _COMPILED:
        for pattern in patterns:
            if pattern.search(normalized):
                return intent
    return INTENT_GENERAL


def normalize_question_key(text):
    """Build a stable dedupe key for unanswered-question aggregation.

    Keeps the alphabetic content only, so "قیمت دوره؟؟؟" and "قیمت دوره"
    aggregate into the same row.
    """
    normalized = _normalize(text).strip()[:400]
    tokens = []
    for token in re.findall(r"[\w\u0600-\u06FF]+", normalized):
        if token in _STOPWORDS or len(token) <= 1:
            continue
        token = token.translate(_KEY_FOLD)
        # A pattern like \w can keep joining trailing punctuation on
        # Persian question marks; strip any non-letter tail characters.
        token = token.rstrip(_ARABIC_PUNCT + string.punctuation)
        if token:
            tokens.append(token)
    key = " ".join(tokens)[:400]
    return key or normalized[:400]
