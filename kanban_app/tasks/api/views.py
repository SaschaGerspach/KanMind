from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import Task
from ...boards.models import Board
from .serializers import TaskCreateSerializer, TaskUpdateSerializer


class TaskCreateView(generics.CreateAPIView):
    """
    API view for creating a new task within a board.
    Only board members or the board owner can create tasks.
    """
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        board = serializer.validated_data["board"]
        user = self.request.user

        # Check if the user is either the board owner or a board member
        if not (board.owner_id == user.id or board.members.filter(pk=user.id).exists()):
            raise PermissionDenied(
                "You must be a member of this board to create a task."
            )

        # Save the task with the current user as creator
        serializer.save(board=board, created_by=user)


class AssignedToMeTaskListView(generics.ListAPIView):
    """
    API view that lists all tasks assigned to the current user.
    """
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingTaskListView(generics.ListAPIView):
    """
    API view that lists all tasks where the current user is set as reviewer.
    """
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(reviewer=user)


class TaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating (PATCH), or deleting a single task.
    Access is restricted to board members or the board owner.
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "task_id"
    queryset = Task.objects.all()

    def get_serializer_class(self):
        # Use a different serializer when updating tasks
        if self.request.method.upper() == "PATCH":
            return TaskUpdateSerializer
        return TaskCreateSerializer

    def get_object(self):
        """
        Fetch the task and ensure the requesting user has access
        (must be board owner or board member).
        """
        task = get_object_or_404(Task, id=self.kwargs["task_id"])
        user = self.request.user
        board = task.board

        is_owner = board.owner_id == user.id
        is_member = board.members.filter(id=user.id).exists()

        if not (is_owner or is_member):
            raise PermissionDenied(
                "You are not a member of this board and cannot access this task."
            )
        return task

    def perform_destroy(self, instance: Task):
        """
        Delete a task only if the requesting user is either:
        - the creator of the task, or
        - the owner of the board.
        """
        user = self.request.user
        board_owner = instance.board.owner
        if instance.created_by != user and board_owner != user:
            raise PermissionDenied(
                "Only the task creator or the board owner can delete this task."
            )
        instance.delete()
