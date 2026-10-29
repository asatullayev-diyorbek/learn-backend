from rest_framework import serializers

from .models import Category, Course, Instructor


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


class CourseDetailSerializer(CourseListSerializer):
    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ["description"]


class CourseMineSerializer(CourseListSerializer):
    """Profile page shape: the catalog card fields plus when the user enrolled."""

    enrolled_at = serializers.DateTimeField(read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ["enrolled_at"]
