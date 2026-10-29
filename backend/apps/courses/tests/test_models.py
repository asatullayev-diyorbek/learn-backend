import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction

from apps.courses import services
from apps.courses.models import Category, Course, Enrollment, Instructor

pytestmark = pytest.mark.django_db


def test_category_course_count_only_counts_published(category, instructor, make_course):
    other = Category.objects.create(name="Frontend", slug="frontend")
    Category.objects.create(name="Ma'lumotlar bazalari", slug="malumotlar-bazalari")
    make_course()
    make_course()
    make_course(is_published=False)
    make_course(category=other)

    counts = {c.slug: c.course_count for c in services.categories_with_course_count()}
    assert counts == {"backend": 2, "frontend": 1, "malumotlar-bazalari": 0}


def test_categories_ordered_by_name():
    Category.objects.create(name="Mobil dasturlash", slug="mobil-dasturlash")
    Category.objects.create(name="Backend", slug="backend")
    Category.objects.create(name="Frontend", slug="frontend")
    names = [c.name for c in services.categories_with_course_count()]
    assert names == ["Backend", "Frontend", "Mobil dasturlash"]


def test_enrollment_is_unique_per_user_and_course(make_course, make_user):
    course = make_course()
    user = make_user()
    Enrollment.objects.create(user=user, course=course)
    with pytest.raises(IntegrityError), transaction.atomic():
        Enrollment.objects.create(user=user, course=course)


def test_enroll_and_unenroll_services_are_idempotent(make_course, make_user):
    course = make_course()
    user, other = make_user(), make_user()

    assert services.enroll(user, course) == 1
    assert services.enroll(user, course) == 1
    assert services.enroll(other, course) == 2
    assert Enrollment.objects.filter(user=user, course=course).count() == 1

    assert services.unenroll(user, course) == 1
    assert services.unenroll(user, course) == 1


def test_published_courses_annotations(make_course, make_user):
    course = make_course()
    make_course(is_published=False)
    user, other = make_user(), make_user()
    services.enroll(user, course)

    rows = list(services.published_courses(user))
    assert [c.id for c in rows] == [course.id]
    assert rows[0].enrolled_count == 1
    assert rows[0].is_enrolled is True

    assert services.published_courses(other).get().is_enrolled is False
    assert services.published_courses(None).get().is_enrolled is False


@pytest.mark.parametrize("reserved_slug", ["categories", "mine"])
def test_course_slug_cannot_be_a_reserved_literal_path(category, instructor, reserved_slug):
    # urls.py registers "categories/" and "mine/" above "<slug>/", so a
    # course slugged either way would be permanently unreachable by its own
    # detail URL.
    course = Course(
        title="Noto'g'ri slug",
        slug=reserved_slug,
        summary="x",
        description="x",
        category=category,
        instructor=instructor,
    )
    with pytest.raises(ValidationError):
        course.full_clean()


def test_category_with_courses_cannot_be_deleted(category, make_course):
    from django.db.models import ProtectedError

    make_course()
    with pytest.raises(ProtectedError):
        category.delete()


def test_seed_courses_is_idempotent():
    call_command("seed_courses")
    counts = (Category.objects.count(), Instructor.objects.count(), Course.objects.count())
    assert counts[0] >= 3 and counts[1] >= 3 and counts[2] >= 8

    call_command("seed_courses")
    assert (Category.objects.count(), Instructor.objects.count(), Course.objects.count()) == counts
    assert not Course.objects.exclude(cover_image_url="").exists()
