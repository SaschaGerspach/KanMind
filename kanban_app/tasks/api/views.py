from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from ...permissions import (
    IsBoardOwner,
    IsBoardMember,
    IsBoardOwnerOrMember,
    CanCreateTaskOnBoard,
    CanDeleteTaskIfCreatorOrBoardOwner,
)
from ..models import Task
from ...boards.models import Board
from .serializers import TaskCreateSerializer, TaskUpdateSerializer


class TaskCreateView(generics.CreateAPIView):
    """
    Create a new task in a board.
    Only board members or the board owner are allowed.
    """
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated, CanCreateTaskOnBoard]

    def perform_create(self, serializer):
        board = serializer.validated_data["board"]
        user = self.request.user

        # Additional runtime check; permission above guards this pre-object.
        if not (
            board.owner_id == user.id or board.members.filter(pk=user.id).exists()
        ):
            raise PermissionDenied(
                "You must be a member of this board to create a task."
            )

        serializer.save(board=board, created_by=user)


class AssignedToMeTaskListView(generics.ListAPIView):
    """List all tasks assigned to the current user."""
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingTaskListView(generics.ListAPIView):
    """List all tasks where the current user is the reviewer."""
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(reviewer=user)


class TaskDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (PATCH), or delete a single task.

    Method-specific permissions:
    - GET:   board owner OR member
    - PATCH: board owner OR member (adjust here if only owner may edit)
    - DELETE: board owner OR task creator (extra rule handled by permission)
    """
    lookup_url_kwarg = "task_id"
    queryset = Task.objects.all()

    def get_permissions(self):
        m = self.request.method
        if m == "GET":
            perms = [IsAuthenticated, IsBoardOwnerOrMember]
        elif m in ("PUT", "PATCH"):
            perms = [IsAuthenticated, IsBoardOwnerOrMember]  # or IsBoardOwner
        elif m == "DELETE":
            perms = [
                IsAuthenticated,
                IsBoardOwnerOrMember,
                CanDeleteTaskIfCreatorOrBoardOwner,
            ]
        else:
            perms = [IsAuthenticated]
        return [p() for p in perms]

    def get_serializer_class(self):
        return (
            TaskUpdateSerializer
            if self.request.method.upper() == "PATCH"
            else TaskCreateSerializer
        )

    def get_object(self):
        # Object-level permissions are checked after retrieving the object.
        return get_object_or_404(Task, id=self.kwargs["task_id"])

    def perform_destroy(self, instance: Task):
        # Special delete rule is enforced by CanDeleteTaskIfCreatorOrBoardOwner.
        instance.delete()
