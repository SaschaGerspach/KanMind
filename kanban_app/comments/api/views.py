from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from ...tasks.models import Task
from ..models import Comment
from .serializers import CommentCreateSerializer, CommentSerializer


class CommentListView(generics.ListAPIView):
    """
    API view to list all comments for a given task.
    Accessible only if the requesting user is a member of the task's board.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Retrieve the related task by ID from the URL
        task_id = self.kwargs["task_id"]
        task = get_object_or_404(Task, id=task_id)

        # Ensure the requesting user is a member of the board
        user = self.request.user
        if not task.board.members.filter(id=user.id).exists():
            raise PermissionDenied("You are not a member of this board.")

        # Return all comments related to the task, ordered by creation date
        return Comment.objects.filter(task=task).order_by("created_at")


class CommentCreateView(generics.CreateAPIView):
    """
    API view to create a new comment on a task.
    Only board members are allowed to comment.
    """
    serializer_class = CommentCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Retrieve the task to which the comment should be added
        task = get_object_or_404(Task, pk=self.kwargs["task_id"])
        user = self.request.user

        # Verify the user is part of the task's board
        if not task.board.members.filter(pk=user.id).exists():
            raise PermissionDenied(
                "You must be a member of this board to comment on this task."
            )

        # Save the comment with the task and the current user as author
        serializer.save(task=task, author=user)


class CommentDeleteView(generics.DestroyAPIView):
    """
    API view to delete a specific comment from a task.
    - The requesting user must be either:
        * the board owner, or
        * the comment's author
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        task_id = self.kwargs["task_id"]
        comment_id = self.kwargs["comment_id"]

        # Ensure the task exists
        task = get_object_or_404(Task, pk=task_id)

        # Check if the user is at least a board member or the board owner
        is_member = task.board.members.filter(pk=user.id).exists()
        is_owner = task.board.owner_id == user.id
        if not (is_member or is_owner):
            raise PermissionDenied(
                "You must be a board member to delete a comment of this task."
            )

        # Ensure the comment exists and belongs to the task
        comment = get_object_or_404(Comment, pk=comment_id, task=task)

        # Only the comment's author can delete it
        if comment.author_id != user.id:
            raise PermissionDenied("Only the author can delete this comment.")

        return comment
