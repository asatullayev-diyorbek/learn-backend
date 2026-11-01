from django.db.models import Count, Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.submissions.models import VideoSubmission
from . import services
from .models import Topic
from .serializers import (
    CategorySerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CourseMineSerializer,
    TopicDetailSerializer,
)


class CoursePagination(PageNumberPagination):
    page_size = 9
    page_query_param = "page"


def _not_found():
    return Response({"detail": "not_found"}, status=404)


def _not_authenticated():
    # Same shape as accounts' /me endpoint. Returned explicitly because DRF
    # would answer 403 for SessionAuthentication-only views.
    return Response({"detail": "not_authenticated"}, status=401)


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = services.categories_with_course_count()
        return Response(CategorySerializer(categories, many=True).data)


class CourseListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        courses = services.filter_courses(
            services.published_courses(request.user),
            category=request.query_params.get("category"),
            level=request.query_params.get("level"),
            search=request.query_params.get("search"),
        )
        paginator = CoursePagination()
        page = paginator.paginate_queryset(courses, request, view=self)
        return paginator.get_paginated_response(CourseListSerializer(page, many=True).data)


class CourseDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        course = (
            services.published_courses(request.user)
            .prefetch_related("topics")
            .filter(slug=slug)
            .first()
        )
        if course is None:
            return _not_found()
        return Response(CourseDetailSerializer(course).data)


class TopicDetailView(APIView):
    """GET /api/courses/<slug>/topics/<topic_id>/ — lesson detail page."""

    permission_classes = [AllowAny]

    def get(self, request, slug, topic_id):
        course = (
            services.published_courses(request.user)
            .filter(slug=slug)
            .first()
        )
        if course is None:
            return _not_found()

        course_topics = list(
            Topic.objects.filter(course=course)
            .annotate(
                video_count=Count(
                    "video_submissions",
                    filter=Q(
                        video_submissions__status=VideoSubmission.STATUS_APPROVED,
                        video_submissions__youtube_video_id__gt="",
                    ),
                )
            )
            .order_by("order", "id")
        )

        topic = next((t for t in course_topics if t.id == topic_id), None)
        if topic is None:
            return _not_found()

        topic.course = course

        approved_videos = list(
            VideoSubmission.objects.filter(
                topic=topic,
                status=VideoSubmission.STATUS_APPROVED,
            )
            .exclude(youtube_video_id="")
            .select_related("student")
            .order_by("-reviewed_at", "-created_at")
        )

        serializer = TopicDetailSerializer(
            topic,
            context={
                "course_topics": course_topics,
                "approved_videos": approved_videos,
            },
        )
        return Response(serializer.data)


class MyCoursesView(APIView):
    """GET /api/courses/mine/ — the profile page's enrolled-courses list.

    Unpaginated: a person's own enrollment count is small, and the profile
    page has no need for page/category/level filtering.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return _not_authenticated()
        courses = services.enrolled_courses(request.user)
        return Response(CourseMineSerializer(courses, many=True).data)


class CourseEnrollView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, slug):
        if not request.user.is_authenticated:
            return _not_authenticated()
        course = services.get_published_course(slug)
        if course is None:
            return _not_found()
        enrolled_count = services.enroll(request.user, course)
        return Response({"status": "enrolled", "enrolled_count": enrolled_count})

    def delete(self, request, slug):
        if not request.user.is_authenticated:
            return _not_authenticated()
        course = services.get_published_course(slug)
        if course is None:
            return _not_found()
        enrolled_count = services.unenroll(request.user, course)
        return Response({"status": "not_enrolled", "enrolled_count": enrolled_count})
