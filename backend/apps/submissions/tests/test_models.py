import pytest
from apps.accounts.models import User
from apps.courses.models import Category, Course, Instructor, Topic
from apps.submissions.models import VideoSubmission


@pytest.mark.django_db
def test_video_submission_creation_and_str():
    user = User.objects.create(username="tg_12345", first_name="Ali")
    category = Category.objects.create(name="Backend", slug="backend")
    instructor = Instructor.objects.create(full_name="Ustoz")
    course = Course.objects.create(
        title="Django kursi",
        slug="django-kursi",
        summary="Qisqa",
        description="Batafsil",
        category=category,
        instructor=instructor,
    )
    topic = Topic.objects.create(course=course, title="1-dars: Kirish", order=1)

    submission = VideoSubmission.objects.create(
        student=user,
        telegram_file_id="BAACAgIAAxkBAAE...",
        status=VideoSubmission.STATUS_AWAITING_TOPIC,
    )

    assert submission.status == "awaiting_topic"
    assert submission.topic is None
    assert "Mavzusiz" in str(submission)
    assert submission.youtube_url == ""

    # Bind topic
    submission.topic = topic
    submission.save()
    assert "1-dars: Kirish" in str(submission)

    # Set YouTube video ID
    submission.youtube_video_id = "dQw4w9WgXcQ"
    submission.save()
    assert submission.youtube_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
