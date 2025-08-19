from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateDestroyAPIView


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

        serializer.save(board=board, created_by=user)

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
    
# class TaskUpdateView(generics.UpdateAPIView):
#     queryset = Task.objects.all()
#     serializer_class = TaskUpdateSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         task = get_object_or_404(Task, id=self.kwargs['task_id'])
#         user = self.request.user

#         # prüfen, ob User Mitglied des Boards ist
#         if not task.board.members.filter(id=user.id).exists():
#             raise PermissionDenied("You are not a member of this board and cannot update this task.")

#         return task

# class TaskDeleteView(generics.DestroyAPIView):
#     queryset = Task.objects.all()
#     serializer_class = TaskCreateSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_destroy(self, instance):
#         user = self.request.user
#         board_owner = instance.board.owner
#         if instance.created_by != user and board_owner != user:
#             raise PermissionDenied("Only the task creator or the board owner can delete this task.")
#         instance.delete()











class TaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    """
    Kombiniert:
      - GET    /api/tasks/<task_id>/
      - PATCH  /api/tasks/<task_id>/
      - DELETE /api/tasks/<task_id>/
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "task_id"

    # Basis-Query – bewusst simple gehalten (minimaler Eingriff)
    queryset = Task.objects.all()

    def get_serializer_class(self):
        # Wie bisher: fürs PATCH den Update-Serializer,
        # für GET/DELETE (Response leer) deinen TaskCreateSerializer als „Output“
        if self.request.method.upper() == "PATCH":
            return TaskUpdateSerializer
        return TaskCreateSerializer

    def get_object(self):
        """
        Holt das Task-Objekt und prüft wie in deiner UpdateView,
        dass der User das Board nutzen darf.
        (Owner wird hier zusätzlich erlaubt, falls er nicht in M2M-members steht.)
        """
        task = get_object_or_404(Task, id=self.kwargs["task_id"])
        user = self.request.user
        board = task.board

        is_owner = (board.owner_id == user.id)
        is_member = board.members.filter(id=user.id).exists()

        if not (is_owner or is_member):
            # gleiche Semantik wie vorher – nur mit Owner-„Ausnahme“
            raise PermissionDenied(
                "You are not a member of this board and cannot access this task."
            )
        return task

    def perform_destroy(self, instance: Task):
        """
        Deine bisherige Delete-Prüfung:
        Löschen darf Ersteller ODER Board-Owner.
        """
        user = self.request.user
        board_owner = instance.board.owner
        if instance.created_by != user and board_owner != user:
            raise PermissionDenied(
                "Only the task creator or the board owner can delete this task."
            )
        instance.delete()