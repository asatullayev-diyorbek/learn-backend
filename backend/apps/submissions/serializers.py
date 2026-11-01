from rest_framework import serializers

from apps.courses.models import Course, Topic
from .models import VideoSubmission


class SubmissionCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "title", "slug"]


class SubmissionTopicSerializer(serializers.ModelSerializer):
    course = SubmissionCourseSerializer(read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "title", "order", "course"]


class VideoSubmissionSerializer(serializers.ModelSerializer):
    topic = SubmissionTopicSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    youtube_url = serializers.CharField(read_only=True)

    class Meta:
        model = VideoSubmission
        fields = [
            "id",
            "student_id",
            "telegram_file_id",
            "topic",
            "status",
            "status_display",
            "youtube_video_id",
            "youtube_url",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]


class BindTopicSerializer(serializers.Serializer):
    topic_id = serializers.IntegerField(required=True)

    def validate_topic_id(self, value):
        try:
            topic = Topic.objects.select_related("course").get(pk=value)
        except Topic.DoesNotExist:
            raise serializers.ValidationError("Ko'rsatilgan mavzu (Topic) topilmadi.")
        return topic


class AvailableTopicItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "title", "order"]


class AvailableCourseTopicsSerializer(serializers.ModelSerializer):
    topics = AvailableTopicItemSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "slug", "topics"]
