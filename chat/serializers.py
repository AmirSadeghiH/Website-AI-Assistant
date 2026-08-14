import re

from rest_framework import serializers


CONVERSATION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
MAX_HISTORY_ITEMS = 8
MAX_HISTORY_CONTENT_LENGTH = 1600
MAX_METADATA_BYTES = 4096


class HistoryItemSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=("user", "assistant"))
    content = serializers.CharField(
        max_length=MAX_HISTORY_CONTENT_LENGTH,
        trim_whitespace=True,
    )


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000, trim_whitespace=True)
    conversation_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
    )
    history = HistoryItemSerializer(
        many=True,
        required=False,
        default=list,
    )

    def validate_message(self, value):
        if not value:
            raise serializers.ValidationError("The message is required.")
        return value

    def validate_conversation_id(self, value):
        if value and not CONVERSATION_ID_RE.fullmatch(value):
            raise serializers.ValidationError("Invalid conversation id.")
        return value

    def validate_history(self, value):
        return value[-MAX_HISTORY_ITEMS:]


class HistoryQuerySerializer(serializers.Serializer):
    conversation_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
    )

    def validate_conversation_id(self, value):
        if value and not CONVERSATION_ID_RE.fullmatch(value):
            raise serializers.ValidationError("Invalid conversation id.")
        return value


class EventSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
    )
    event_type = serializers.CharField(max_length=40)
    metadata = serializers.JSONField(required=False, default=dict)

    def validate_conversation_id(self, value):
        if value and not CONVERSATION_ID_RE.fullmatch(value):
            raise serializers.ValidationError("Invalid conversation id.")
        return value

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
    conversation_id = serializers.CharField(max_length=100)
    message_id = serializers.IntegerField(min_value=1)
    feedback = serializers.ChoiceField(choices=("helpful", "not_helpful"))

    def validate_conversation_id(self, value):
        if not CONVERSATION_ID_RE.fullmatch(value):
            raise serializers.ValidationError("Invalid conversation id.")
        return value
