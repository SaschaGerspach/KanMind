from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from kanban_app.tasks.models import Task
from kanban_app.comments.models import Comment
from .serializers import CommentCreateSerializer

class CommentCreateView(generics.CreateAPIView):
    """
    POST /api/tasks/{task_id}/comments/
    Erzeugt einen Kommentar zum Task. Der Author ist der eingeloggte User.
    Voraussetzung: User ist Mitglied des Boards, zu dem der Task gehört.
    """
    serializer_class = CommentCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs["task_id"])
        user = self.request.user

        # Spezifikation: User muss Mitglied des Boards sein (Owner zählt hier NICHT automatisch).
        if not task.board.members.filter(pk=user.id).exists():
            raise PermissionDenied("You must be a member of this board to comment on this task.")

        serializer.save(task=task, author=user)
