from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from ..models import Task
from ...boards.models import Board

from .serializers import TaskCreateSerializer


class TaskCreateView(generics.CreateAPIView):
    """
    POST /api/tasks/
    Erstellt einen neuen Task in einem Board.
    """
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        board = serializer.validated_data["board"]
        user = self.request.user

        # Zugriffskontrolle: nur Mitglieder des Boards dürfen Tasks anlegen
        if not (board.owner_id == user.id or board.members.filter(pk=user.id).exists()):
            raise PermissionDenied("You must be a member of this board to create a task.")

        serializer.save()
