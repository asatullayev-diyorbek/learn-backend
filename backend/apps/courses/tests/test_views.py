import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.courses.models import Category, Course, Enrollment

pytestmark = pytest.mark.django_db

LIST_URL = "/api/courses/"
CARD_KEYS = {
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
}


def detail_url(slug):
    return reverse("courses:course-detail", kwargs={"slug": slug})


def enroll_url(slug):
    return reverse("courses:course-enroll", kwargs={"slug": slug})


def mine_url():
    return reverse("courses:course-mine")


def result_slugs(response):
    return {item["slug"] for item in response.data["results"]}


# --------------------------------------------------------------------------
# Categories
# --------------------------------------------------------------------------


def test_categories_contract_shape(client, category, make_course):
    make_course()
    make_course(is_published=False)
    Category.objects.create(name="Frontend", slug="frontend")

    response = client.get(reverse("courses:category-list"))
    assert response.status_code == 200
    assert response.data == [
        {"id": category.id, "name": "Backend", "slug": "backend", "course_count": 1},
        {"id": Category.objects.get(slug="frontend").id, "name": "Frontend", "slug": "frontend", "course_count": 0},
    ]


# --------------------------------------------------------------------------
# List + filters + pagination
# --------------------------------------------------------------------------


def test_list_contract_shape(client, category, instructor, make_course):
    course = make_course(slug="python-asoslari", title="Python asoslari")

    assert reverse("courses:course-list") == LIST_URL
    response = client.get(LIST_URL)
    assert response.status_code == 200
    assert set(response.data.keys()) == {"count", "next", "previous", "results"}
    assert response.data["count"] == 1
    item = response.data["results"][0]
    assert set(item.keys()) == CARD_KEYS
    assert item == {
        "id": course.id,
        "slug": "python-asoslari",
        "title": "Python asoslari",
        "summary": course.summary,
        "level": "beginner",
        "category": {"id": category.id, "name": "Backend", "slug": "backend"},
        "instructor": {"id": instructor.id, "full_name": "Diyorbek Asatullayev"},
        "cover_image_url": "",
        "enrolled_count": 0,
        "is_enrolled": False,
    }


def test_list_excludes_unpublished(client, make_course):
    make_course(slug="visible")
    make_course(slug="hidden", is_published=False)
    assert result_slugs(client.get(LIST_URL)) == {"visible"}


def test_list_filters_by_category(client, make_course):
    frontend = Category.objects.create(name="Frontend", slug="frontend")
    make_course(slug="b1")
    make_course(slug="f1", category=frontend)

    assert result_slugs(client.get(LIST_URL, {"category": "frontend"})) == {"f1"}
    assert result_slugs(client.get(LIST_URL, {"category": "backend"})) == {"b1"}


def test_list_filters_by_level(client, make_course):
    make_course(slug="b", level=Course.LEVEL_BEGINNER)
    make_course(slug="i", level=Course.LEVEL_INTERMEDIATE)
    make_course(slug="a", level=Course.LEVEL_ADVANCED)

    assert result_slugs(client.get(LIST_URL, {"level": "intermediate"})) == {"i"}
    assert result_slugs(client.get(LIST_URL, {"level": "advanced"})) == {"a"}


def test_list_search_matches_title_or_summary_case_insensitively(client, make_course):
    make_course(slug="by-title", title="Python asoslari", summary="Boshlang'ich kurs")
    make_course(slug="by-summary", title="Django", summary="PYTHON bilan veb")
    make_course(slug="no-match", title="React", summary="Frontend")

    response = client.get(LIST_URL, {"search": "python"})
    assert result_slugs(response) == {"by-title", "by-summary"}


def test_list_filters_combine(client, make_course):
    frontend = Category.objects.create(name="Frontend", slug="frontend")
    make_course(slug="match", title="React", category=frontend, level=Course.LEVEL_ADVANCED)
    make_course(slug="wrong-level", title="React", category=frontend)
    make_course(slug="wrong-cat", title="React", level=Course.LEVEL_ADVANCED)

    response = client.get(LIST_URL, {"category": "frontend", "level": "advanced", "search": "react"})
    assert result_slugs(response) == {"match"}


@pytest.mark.parametrize("params", [{"level": "expert"}, {"category": "does-not-exist"}])
def test_list_invalid_filter_values_return_empty_results(client, make_course, params):
    make_course()
    response = client.get(LIST_URL, params)
    assert response.status_code == 200
    assert response.data["count"] == 0
    assert response.data["results"] == []


def test_list_pagination_shape(client, make_course):
    for _ in range(11):
        make_course()

    first = client.get(LIST_URL)
    assert first.data["count"] == 11
    assert len(first.data["results"]) == 9
    assert first.data["previous"] is None
    assert first.data["next"].endswith("/api/courses/?page=2")

    second = client.get(LIST_URL, {"page": 2})
    assert len(second.data["results"]) == 2
    assert second.data["next"] is None
    assert second.data["previous"] is not None

    all_slugs = result_slugs(first) | result_slugs(second)
    assert len(all_slugs) == 11


def test_list_query_count_does_not_scale_with_page_size(make_course, auth_client):
    c, user = auth_client()
    course = make_course()
    Enrollment.objects.create(user=user, course=course)

    with CaptureQueriesContext(connection) as one:
        c.get(LIST_URL)
    for _ in range(8):
        make_course()
    with CaptureQueriesContext(connection) as nine:
        response = c.get(LIST_URL)

    assert len(response.data["results"]) == 9
    assert len(nine.captured_queries) == len(one.captured_queries)


# --------------------------------------------------------------------------
# Detail
# --------------------------------------------------------------------------


def test_detail_returns_card_fields_plus_description(client, make_course):
    course = make_course(slug="python-asoslari", description="To'liq tavsif")
    response = client.get(detail_url("python-asoslari"))
    assert response.status_code == 200
    assert set(response.data.keys()) == CARD_KEYS | {"description"}
    assert response.data["description"] == "To'liq tavsif"
    assert response.data["id"] == course.id
    assert response.data["is_enrolled"] is False


def test_detail_missing_slug_is_404(client):
    response = client.get(detail_url("yoq-kurs"))
    assert response.status_code == 404
    assert response.data == {"detail": "not_found"}


def test_detail_unpublished_is_404(client, make_course):
    make_course(slug="draft", is_published=False)
    response = client.get(detail_url("draft"))
    assert response.status_code == 404
    assert response.data == {"detail": "not_found"}


# --------------------------------------------------------------------------
# Enroll / unenroll
# --------------------------------------------------------------------------


@pytest.mark.parametrize("method", ["post", "delete"])
def test_enroll_requires_authentication(client, make_course, method):
    course = make_course()
    response = getattr(client, method)(enroll_url(course.slug))
    assert response.status_code == 401
    assert response.data == {"detail": "not_authenticated"}
    assert not Enrollment.objects.exists()


def test_enroll_is_idempotent(make_course, auth_client):
    course = make_course()
    c, user = auth_client()

    first = c.post(enroll_url(course.slug))
    assert first.status_code == 200
    assert first.data == {"status": "enrolled", "enrolled_count": 1}

    second = c.post(enroll_url(course.slug))
    assert second.status_code == 200
    assert second.data == {"status": "enrolled", "enrolled_count": 1}
    assert Enrollment.objects.filter(user=user, course=course).count() == 1

    other_client, _ = auth_client()
    third = other_client.post(enroll_url(course.slug))
    assert third.data == {"status": "enrolled", "enrolled_count": 2}


def test_unenroll_is_idempotent(make_course, auth_client):
    course = make_course()
    c, user = auth_client()
    other_client, _ = auth_client()
    other_client.post(enroll_url(course.slug))

    # Not enrolled yet: still a clean 200.
    never = c.delete(enroll_url(course.slug))
    assert never.status_code == 200
    assert never.data == {"status": "not_enrolled", "enrolled_count": 1}

    c.post(enroll_url(course.slug))
    first = c.delete(enroll_url(course.slug))
    assert first.status_code == 200
    assert first.data == {"status": "not_enrolled", "enrolled_count": 1}

    second = c.delete(enroll_url(course.slug))
    assert second.status_code == 200
    assert second.data == {"status": "not_enrolled", "enrolled_count": 1}
    assert not Enrollment.objects.filter(user=user).exists()


@pytest.mark.parametrize("method", ["post", "delete"])
def test_enroll_missing_or_unpublished_course_is_404(make_course, auth_client, method):
    make_course(slug="draft", is_published=False)
    c, _ = auth_client()
    for slug in ("draft", "yoq-kurs"):
        response = getattr(c, method)(enroll_url(slug))
        assert response.status_code == 404
        assert response.data == {"detail": "not_found"}
    assert not Enrollment.objects.exists()


def test_is_enrolled_is_per_user_and_never_leaks(client, make_course, auth_client):
    enrolled_course = make_course(slug="a")
    make_course(slug="b")
    alice, _ = auth_client("alice")
    bob, _ = auth_client("bob")

    alice.post(enroll_url("a"))

    def flags(c):
        return {item["slug"]: item["is_enrolled"] for item in c.get(LIST_URL).data["results"]}

    assert flags(alice) == {"a": True, "b": False}
    assert flags(bob) == {"a": False, "b": False}
    assert flags(client) == {"a": False, "b": False}

    assert alice.get(detail_url("a")).data["is_enrolled"] is True
    assert bob.get(detail_url("a")).data["is_enrolled"] is False
    assert client.get(detail_url("a")).data["is_enrolled"] is False

    # enrolled_count is global, is_enrolled is personal.
    assert bob.get(detail_url("a")).data["enrolled_count"] == 1

    alice.delete(enroll_url("a"))
    assert flags(alice) == {"a": False, "b": False}
    assert enrolled_course.enrollments.count() == 0


def test_enroll_enforces_csrf_for_session_users(make_course, make_user):
    """Same CSRF protection as the rest of the app's session-authenticated POSTs."""
    from rest_framework.test import APIClient

    course = make_course()
    c = APIClient(enforce_csrf_checks=True)
    c.force_login(make_user())

    response = c.post(enroll_url(course.slug))
    assert response.status_code == 403
    assert not Enrollment.objects.exists()


def test_mine_requires_authentication(client):
    response = client.get(mine_url())
    assert response.status_code == 401
    assert response.data == {"detail": "not_authenticated"}


def test_mine_lists_only_my_published_enrollments_most_recent_first(make_course, auth_client):
    c, user = auth_client()
    other_client, other_user = auth_client()

    a = make_course(title="A")
    b = make_course(title="B")
    unpublished = make_course(title="C", is_published=False)
    not_mine = make_course(title="D")

    c.post(enroll_url(a.slug))
    c.post(enroll_url(unpublished.slug))
    other_client.post(enroll_url(not_mine.slug))
    c.post(enroll_url(b.slug))  # enrolled last -> listed first

    response = c.get(mine_url())
    assert response.status_code == 200
    titles = [item["title"] for item in response.data]
    assert titles == ["B", "A"]
    assert all(item["is_enrolled"] is True for item in response.data)
    assert set(response.data[0].keys()) == CARD_KEYS | {"enrolled_at"}


def test_mine_enrolled_count_is_global_not_just_mine(make_course, auth_client):
    """A course's enrolled_count on /mine/ must not collapse to 1 (regression:
    filtering and then Count()-ing the same relation in one queryset)."""
    course = make_course()
    c, _ = auth_client()
    other_client, _ = auth_client()
    c.post(enroll_url(course.slug))
    other_client.post(enroll_url(course.slug))

    response = c.get(mine_url())
    assert response.data[0]["enrolled_count"] == 2


def test_mine_is_empty_for_a_user_with_no_enrollments(auth_client):
    c, _ = auth_client()
    response = c.get(mine_url())
    assert response.status_code == 200
    assert response.data == []
