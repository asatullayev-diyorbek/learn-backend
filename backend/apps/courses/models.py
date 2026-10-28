from django.core.exceptions import ValidationError
from django.db import models

# "categories/" is a literal path registered above "<slug>/" in urls.py so
# GET /api/courses/categories/ always reaches the category list — which
# means a course slug of "categories" would be permanently unreachable by
# its own detail URL. Block it at the model level, not just in urls.py.
RESERVED_COURSE_SLUGS = {"categories"}


def validate_course_slug(value):
    if value in RESERVED_COURSE_SLUGS:
        raise ValidationError('"%(value)s" slug band qilingan va kurslar uchun ishlatilmaydi.', params={"value": value})


class Category(models.Model):
    """A catalog grouping used for filtering (e.g. Backend, Frontend)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)

    def __str__(self):
        return self.name


class Instructor(models.Model):
    """Display-only instructor profile.

    Deliberately NOT linked to a User: instructor accounts/auth are out of
    scope for this phase, content is managed through Django admin.
    """

    full_name = models.CharField(max_length=150)
    title = models.CharField(max_length=150, blank=True)  # e.g. "Backend dasturchi"
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.full_name


class Course(models.Model):
    """A catalog entry. Only is_published=True courses are ever exposed via the API."""

    LEVEL_BEGINNER = "beginner"
    LEVEL_INTERMEDIATE = "intermediate"
    LEVEL_ADVANCED = "advanced"
    LEVEL_CHOICES = [
        (LEVEL_BEGINNER, "Boshlang'ich"),
        (LEVEL_INTERMEDIATE, "O'rta"),
        (LEVEL_ADVANCED, "Yuqori"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, validators=[validate_course_slug])
    summary = models.CharField(max_length=300)  # card blurb
    description = models.TextField()  # detail page body
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="courses")
    instructor = models.ForeignKey(Instructor, on_delete=models.PROTECT, related_name="courses")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=LEVEL_BEGINNER)
    # No media/upload pipeline in this phase; the frontend shows a
    # placeholder when this is blank.
    cover_image_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    """Links one user to one course; unique per (user, course)."""

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "course")]

    def __str__(self):
        return f"Enrollment(user={self.user_id}, course={self.course_id})"
