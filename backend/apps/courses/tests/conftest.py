import itertools

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.courses.models import Category, Course, Instructor

_seq = itertools.count(1)


@pytest.fixture
def category(db):
    return Category.objects.create(name="Backend", slug="backend")


@pytest.fixture
def instructor(db):
    return Instructor.objects.create(full_name="Diyorbek Asatullayev", title="Backend dasturchi")


@pytest.fixture
def make_course(category, instructor):
    def _make(**overrides):
        n = next(_seq)
        fields = {
            "title": f"Kurs {n}",
            "slug": f"kurs-{n}",
            "summary": f"Kurs {n} haqida qisqacha",
            "description": f"Kurs {n} tavsifi",
            "category": category,
            "instructor": instructor,
        }
        fields.update(overrides)
        return Course.objects.create(**fields)

    return _make


@pytest.fixture
def make_user(db):
    def _make(username=None):
        return User.objects.create(username=username or f"tg_{next(_seq)}")

    return _make


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(make_user):
    """Returns (client, user) logged in through a real session cookie."""

    def _make(username=None):
        user = make_user(username)
        c = APIClient()
        c.force_login(user)
        return c, user

    return _make
