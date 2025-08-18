from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


from ..models import Task
from ...boards.models import Board

from .serializers import TaskCreateSerializer, TaskUpdateSerializer


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

class AssignedToMeTaskListView(generics.ListAPIView):
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Nur Tasks zurückgeben, die dem eingeloggten User zugewiesen sind
        return Task.objects.filter(assignee=self.request.user)
    
class ReviewingTaskListView(generics.ListAPIView):
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(reviewer=user)
    
class TaskUpdateView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        task = get_object_or_404(Task, id=self.kwargs['task_id'])
        user = self.request.user

        # prüfen, ob User Mitglied des Boards ist
        if not task.board.members.filter(id=user.id).exists():
            raise PermissionDenied("You are not a member of this board and cannot update this task.")

        return task
