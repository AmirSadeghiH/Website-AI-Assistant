import re

from rest_framework import serializers


CONVERSATION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
MAX_METADATA_BYTES = 4096
# Basic phone sanity: digits, +, -, space, parentheses; 7-20 significant chars.
PHONE_RE = re.compile(r"^[+0-9][0-9\s\-()]{6,24}$")


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000, trim_whitespace=True)
    conversation_id = serializers.RegexField(
        CONVERSATION_ID_RE, required=False, allow_blank=True
    )
    page_url = serializers.URLField(required=False, allow_blank=True, max_length=1000)

    def validate_message(self, value):
        if not value:
            raise serializers.ValidationError("The message is required.")
        return value


class HistoryRequestSerializer(serializers.Serializer):
    conversation_id = serializers.RegexField(CONVERSATION_ID_RE)
    token = serializers.CharField(max_length=64, required=False, allow_blank=True)


class EventSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=40)
    metadata = serializers.JSONField(required=False, default=dict)

    def validate_event_type(self, value):
        from .models import AnalyticsEvent

        valid = {choice[0] for choice in AnalyticsEvent.EVENT_CHOICES}
        if value not in valid:
            raise serializers.ValidationError("Invalid event type.")
        return value

    def validate_metadata(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Metadata must be an object.")
        if len(str(value).encode("utf-8")) > MAX_METADATA_BYTES:
            raise serializers.ValidationError("Metadata is too large.")
        return value


class FeedbackSerializer(serializers.Serializer):
    """Feedback submitted by the widget after the user rates an answer.

    Fields:
    - helpful (bool, required): True = thumbs up, False = thumbs down
    - message_id (int, optional): the assistant message being rated
    - conversation_id + conversation_token (optional): ownership binding
    - comment (str, optional): Optional free-text comment from the user
    """
    helpful = serializers.BooleanField()
    message_id = serializers.IntegerField(required=False, min_value=1)
    conversation_id = serializers.RegexField(
        CONVERSATION_ID_RE, required=False, allow_blank=True
    )
    conversation_token = serializers.CharField(
        max_length=64, required=False, allow_blank=True
    )
    question = serializers.CharField(max_length=4000, required=False, default="")
    answer_preview = serializers.CharField(max_length=1000, required=False, default="")
    session_id = serializers.CharField(max_length=100, required=False, default="")
    comment = serializers.CharField(max_length=1000, required=False, default="")


class LeadSerializer(serializers.Serializer):
    """Visitor-submitted lead (#11). At least one contact channel required."""

    name = serializers.CharField(max_length=200, trim_whitespace=True)
    email = serializers.EmailField(required=False, default="", allow_blank=True)
    phone = serializers.CharField(
        max_length=30, required=False, default="", allow_blank=True
    )
    note = serializers.CharField(max_length=2000, required=False, default="", allow_blank=True)
    conversation_id = serializers.RegexField(
        CONVERSATION_ID_RE, required=False, allow_blank=True
    )
    conversation_token = serializers.CharField(
        max_length=64, required=False, allow_blank=True
    )
    # Honeypot — real visitors never fill this; bots do.
    website = serializers.CharField(required=False, default="", allow_blank=True)

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("The name is too short.")
        return value

    def validate_phone(self, value):
        if value and not PHONE_RE.match(value.replace(" ", "")):
            raise serializers.ValidationError("The phone number is invalid.")
        return value

    def validate(self, attrs):
        if attrs.get("website"):
            # Silently accepted (never stored) to not tip off bots.
            attrs["honeypot_hit"] = True
        if not (attrs.get("email") or attrs.get("phone")):
            raise serializers.ValidationError(
                {"email": "حداقل یکی از ایمیل یا شماره تماس الزامی است."}
            )
        return attrs


class HandoffSerializer(serializers.Serializer):
    """Human handoff request (#12)."""

    channel = serializers.ChoiceField(
        choices=("email", "telegram", "whatsapp", "contact_form")
    )
    message = serializers.CharField(max_length=2000, trim_whitespace=True)
    conversation_id = serializers.RegexField(
        CONVERSATION_ID_RE, required=False, allow_blank=True
    )
    conversation_token = serializers.CharField(
        max_length=64, required=False, allow_blank=True
    )

    def validate_message(self, value):
        if not value:
            raise serializers.ValidationError("The message is required.")
        return value
