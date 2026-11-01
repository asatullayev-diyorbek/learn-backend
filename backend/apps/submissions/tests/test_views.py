import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.courses.models import Category, Course, Instructor, Topic
from apps.submissions.models import VideoSubmission


@pytest.fixture
def course_and_topic():
    category = Category.objects.create(name="Python", slug="python")
    instructor = Instructor.objects.create(full_name="Ustoz")
    course = Course.objects.create(
        title="Python asoslari",
        slug="python-asoslari",
        summary="Qisqa",
        description="Batafsil",
        category=category,
        instructor=instructor,
    )
    topic = Topic.objects.create(course=course, title="O'zgaruvchilar", order=1)
    return course, topic


@pytest.mark.django_db
def test_my_submissions_unauthenticated():
    client = APIClient()
    response = client.get("/api/submissions/mine/")
    assert response.status_code == 401
    assert response.json() == {"detail": "not_authenticated"}


@pytest.mark.django_db
def test_my_submissions_authenticated(course_and_topic):
    course, topic = course_and_topic
    user = User.objects.create(username="tg_student")
    client = APIClient()
    client.force_authenticate(user=user)

    # Initially empty
    response = client.get("/api/submissions/mine/")
    assert response.status_code == 200
    assert response.json() == []

    # Create submission
    submission = VideoSubmission.objects.create(
        student=user,
        topic=topic,
        telegram_file_id="tg_file_abc",
        status=VideoSubmission.STATUS_PENDING_REVIEW,
    )

    response = client.get("/api/submissions/mine/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == submission.id
    assert data[0]["telegram_file_id"] == "tg_file_abc"
    assert data[0]["status"] == "pending_review"
    assert data[0]["topic"]["id"] == topic.id
    assert data[0]["topic"]["title"] == "O'zgaruvchilar"
    assert data[0]["topic"]["course"]["slug"] == "python-asoslari"


@pytest.mark.django_db
def test_bind_topic_success(course_and_topic):
    course, topic = course_and_topic
    user = User.objects.create(username="tg_student")
    submission = VideoSubmission.objects.create(
        student=user,
        telegram_file_id="tg_file_abc",
        status=VideoSubmission.STATUS_AWAITING_TOPIC,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/submissions/{submission.id}/bind/",
        {"topic_id": topic.id},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_review"
    assert data["topic"]["id"] == topic.id


@pytest.mark.django_db
def test_bind_topic_forbidden_for_non_owner(course_and_topic):
    course, topic = course_and_topic
    owner = User.objects.create(username="tg_owner")
    other_user = User.objects.create(username="tg_other")
    submission = VideoSubmission.objects.create(
        student=owner,
        telegram_file_id="tg_file_abc",
        status=VideoSubmission.STATUS_AWAITING_TOPIC,
    )

    client = APIClient()
    client.force_authenticate(user=other_user)

    response = client.post(
        f"/api/submissions/{submission.id}/bind/",
        {"topic_id": topic.id},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_bind_topic_invalid_if_already_bound(course_and_topic):
    course, topic = course_and_topic
    user = User.objects.create(username="tg_student")
    submission = VideoSubmission.objects.create(
        student=user,
        topic=topic,
        telegram_file_id="tg_file_abc",
        status=VideoSubmission.STATUS_PENDING_REVIEW,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/submissions/{submission.id}/bind/",
        {"topic_id": topic.id},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_available_topics(course_and_topic):
    course, topic = course_and_topic
    client = APIClient()
    response = client.get("/api/submissions/available-topics/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    course_data = next(c for c in data if c["id"] == course.id)
    assert len(course_data["topics"]) >= 1
    assert course_data["topics"][0]["title"] == "O'zgaruvchilar"

