from rest_framework import serializers

from apps.submissions.models import VideoSubmission
from .models import Category, Course, Instructor, Topic


class CategorySerializer(serializers.ModelSerializer):
    # Provided by services.categories_with_course_count().
    course_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "course_count"]


class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class InstructorBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = ["id", "full_name"]


class CourseListSerializer(serializers.ModelSerializer):
    """Catalog card shape. Expects a services.published_courses() queryset."""

    category = CategoryBriefSerializer(read_only=True)
    instructor = InstructorBriefSerializer(read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "slug",
            "title",
            "summary",
            "level",
            "category",
            "instructor",
            "cover_image_url",
            "enrolled_count",
            "is_enrolled",
        ]


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "title", "order"]


class LessonVideoAuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="student.id", read_only=True)
    username = serializers.CharField(source="student.username", read_only=True)
    first_name = serializers.CharField(source="student.first_name", read_only=True)
    last_name = serializers.CharField(source="student.last_name", read_only=True)
    telegram_username = serializers.CharField(source="student.telegram_username", read_only=True)


class LessonVideoSerializer(serializers.ModelSerializer):
    author = LessonVideoAuthorSerializer(source="*", read_only=True)
    youtube_url = serializers.CharField(read_only=True)
    embed_url = serializers.SerializerMethodField()

    class Meta:
        model = VideoSubmission
        fields = [
            "id",
            "youtube_video_id",
            "youtube_url",
            "embed_url",
            "author",
            "created_at",
        ]

    def get_embed_url(self, obj: VideoSubmission) -> str:
        if not obj.youtube_video_id:
            return ""
        return f"https://www.youtube.com/embed/{obj.youtube_video_id}"


class TopicNavSerializer(serializers.ModelSerializer):
    video_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Topic
        fields = ["id", "title", "order", "video_count"]


class TopicDetailSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    previous_topic_id = serializers.SerializerMethodField()
    next_topic_id = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id",
            "title",
            "order",
            "course",
            "topics",
            "videos",
            "previous_topic_id",
            "next_topic_id",
        ]

    def get_course(self, obj: Topic) -> dict:
        course = obj.course
        return {
            "id": course.id,
            "slug": course.slug,
            "title": course.title,
            "summary": course.summary,
            "level": course.level,
            "category": CategoryBriefSerializer(course.category).data,
            "instructor": InstructorBriefSerializer(course.instructor).data,
            "is_enrolled": getattr(course, "is_enrolled", False),
        }

    def get_topics(self, obj: Topic) -> list:
        all_topics = self.context.get("course_topics", [])
        return TopicNavSerializer(all_topics, many=True).data

    def get_videos(self, obj: Topic) -> list:
        approved = self.context.get("approved_videos", [])
        return LessonVideoSerializer(approved, many=True).data

    def get_previous_topic_id(self, obj: Topic):
        all_topics = self.context.get("course_topics", [])
        ids = [t.id for t in all_topics]
        try:
            idx = ids.index(obj.id)
            return ids[idx - 1] if idx > 0 else None
        except ValueError:
            return None

    def get_next_topic_id(self, obj: Topic):
        all_topics = self.context.get("course_topics", [])
        ids = [t.id for t in all_topics]
        try:
            idx = ids.index(obj.id)
            return ids[idx + 1] if idx + 1 < len(ids) else None
        except ValueError:
            return None


class CourseDetailSerializer(CourseListSerializer):
    # Topic.Meta.ordering (order, id) means `topics` is already in the
    # right order; .prefetch_related("topics") in the view keeps this to
    # one extra query regardless of how many topics a course has.
    topics = TopicSerializer(many=True, read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ["description", "topics"]


class CourseMineSerializer(CourseListSerializer):
    """Profile page shape: the catalog card fields plus when the user enrolled."""

    enrolled_at = serializers.DateTimeField(read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ["enrolled_at"]
