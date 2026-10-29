from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    CategorySerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CourseMineSerializer,
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
        course = services.published_courses(request.user).filter(slug=slug).first()
        if course is None:
            return _not_found()
        return Response(CourseDetailSerializer(course).data)


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
