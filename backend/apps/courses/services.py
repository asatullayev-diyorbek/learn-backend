"""
Core business logic for the course catalog and enrollment.

Views stay thin and call into here, mirroring apps.accounts.services. All
public-facing course lookups go through published_courses() so an
unpublished course can never leak through the list, the detail page or the
enroll endpoint.
"""

from typing import Optional

from django.db.models import BooleanField, Count, Exists, OuterRef, Q, QuerySet, Value

from .models import Category, Course, Enrollment


def categories_with_course_count() -> QuerySet:
    """All categories, each annotated with its number of PUBLISHED courses."""
    return Category.objects.annotate(
        course_count=Count("courses", filter=Q(courses__is_published=True))
    ).order_by("name")


def published_courses(user=None) -> QuerySet:
    """Published courses with everything the list/detail serializers need.

    One query regardless of page size: category/instructor are joined via
    select_related, enrolled_count is a COUNT annotation and is_enrolled is
    a correlated EXISTS subquery scoped to `user` (always False for
    anonymous users), so nothing is fetched per course.
    """
    if user is not None and user.is_authenticated:
        is_enrolled = Exists(
            Enrollment.objects.filter(user=user, course=OuterRef("pk"))
        )
    else:
        is_enrolled = Value(False, output_field=BooleanField())

    return (
        Course.objects.filter(is_published=True)
        .select_related("category", "instructor")
        .annotate(enrolled_count=Count("enrollments"), is_enrolled=is_enrolled)
        # Deterministic order so pagination never repeats/skips rows.
        .order_by("-created_at", "-id")
    )


def filter_courses(
    queryset: QuerySet,
    category: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet:
    """Apply the catalog's optional query-param filters.

    Unknown category slugs / invalid levels simply match nothing (an empty
    page), the same forgiving behavior as a search that finds no results.
    """
    if category:
        queryset = queryset.filter(category__slug=category)
    if level:
        queryset = queryset.filter(level=level)
    if search:
        search = search.strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(summary__icontains=search)
            )
    return queryset


def get_published_course(slug: str) -> Optional[Course]:
    """Fetch a published course by slug (no annotations), or None."""
    return Course.objects.filter(slug=slug, is_published=True).first()


def enroll(user, course: Course) -> int:
    """Idempotently enroll user in course. Returns the course's enrolled_count.

    get_or_create recovers from the IntegrityError raised by the
    (user, course) unique constraint, so two concurrent calls still end up
    with exactly one Enrollment row.
    """
    Enrollment.objects.get_or_create(user=user, course=course)
    return Enrollment.objects.filter(course=course).count()


def unenroll(user, course: Course) -> int:
    """Idempotently remove user's enrollment. Returns the course's enrolled_count."""
    Enrollment.objects.filter(user=user, course=course).delete()
    return Enrollment.objects.filter(course=course).count()
