import re

from rest_framework import serializers


CONVERSATION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
MAX_METADATA_BYTES = 4096


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000, trim_whitespace=True)

    def validate_message(self, value):
        if not value:
            raise serializers.ValidationError("The message is required.")
        return value


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
    - question (str, optional): The user's original question (for linking)
    - answer_preview (str, optional): First ~300 chars of the AI answer
    - session_id (str, optional): Anonymous browser session identifier
    - comment (str, optional): Optional free-text comment from the user
    """
    helpful = serializers.BooleanField()
    question = serializers.CharField(max_length=4000, required=False, default="")
    answer_preview = serializers.CharField(max_length=1000, required=False, default="")
    session_id = serializers.CharField(max_length=100, required=False, default="")
    comment = serializers.CharField(max_length=1000, required=False, default="")
