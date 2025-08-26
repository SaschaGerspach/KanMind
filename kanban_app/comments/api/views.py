from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from ...tasks.models import Task
from ..models import Comment
from .serializers import CommentCreateSerializer, CommentSerializer
from ...permissions import CanAccessTaskBoardFromURL, IsCommentAuthor


class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET  /tasks/{task_id}/comments/  -> list (board owner/member)
    POST /tasks/{task_id}/comments/  -> create (board owner/member)
    """
    permission_classes = [IsAuthenticated, CanAccessTaskBoardFromURL]

    def get_queryset(self):
        task = get_object_or_404(Task, id=self.kwargs["task_id"])
        return Comment.objects.filter(task=task).order_by("created_at")

    def get_serializer_class(self):
        return (
            CommentCreateSerializer
            if self.request.method == "POST"
            else CommentSerializer
        )

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs["task_id"])
        serializer.save(task=task, author=self.request.user)


class CommentDeleteView(generics.DestroyAPIView):
    """
    DELETE /tasks/{task_id}/comments/{comment_id}/

    Requirements:
    - Board access (owner or member) via CanAccessTaskBoardFromURL.
    - Only the comment's author may delete (IsCommentAuthor).
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, CanAccessTaskBoardFromURL, IsCommentAuthor]

    def get_object(self):
        task = get_object_or_404(Task, pk=self.kwargs["task_id"])
        obj = get_object_or_404(
            Comment, pk=self.kwargs["comment_id"], task=task
        )
        # Apply object-level permissions (e.g., IsCommentAuthor)
        self.check_object_permissions(self.request, obj)
        return obj
