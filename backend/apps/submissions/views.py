from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import VideoSubmission
from .serializers import (
    AvailableCourseTopicsSerializer,
    BindTopicSerializer,
    VideoSubmissionSerializer,
)


def _not_authenticated():
    return Response({"detail": "not_authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


class MySubmissionsView(APIView):
    """GET /api/submissions/mine/ — list the current user's video submissions."""

    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return _not_authenticated()

        submissions = services.get_user_submissions(request.user)
        return Response(VideoSubmissionSerializer(submissions, many=True).data)


class BindTopicView(APIView):
    """POST /api/submissions/<id>/bind/ — bind an awaiting submission to a course Topic."""

    permission_classes = [AllowAny]

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return _not_authenticated()

        submission = get_object_or_404(
            VideoSubmission.objects.select_related("topic", "topic__course"), pk=pk
        )

        if submission.student_id != request.user.id:
            return Response(
                {"detail": "Siz faqat o'zingizning videolaringizni biriktirishingiz mumkin."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if submission.status != VideoSubmission.STATUS_AWAITING_TOPIC:
            return Response(
                {"detail": "Faqat mavzu biriktirilmagan videolarni topshirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BindTopicSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        topic = serializer.validated_data["topic_id"]
        updated_submission = services.bind_submission_topic(submission, topic, request.user)
        return Response(VideoSubmissionSerializer(updated_submission).data, status=status.HTTP_200_OK)


class AvailableTopicsView(APIView):
    """GET /api/submissions/available-topics/ — list available courses and topics for binding."""

    permission_classes = [AllowAny]

    def get(self, request):
        courses = services.get_available_course_topics()
        return Response(AvailableCourseTopicsSerializer(courses, many=True).data)
