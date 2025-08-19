from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from  ...tasks.models import Task
from ..models import Comment
from .serializers import CommentCreateSerializer, CommentSerializer

class CommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs['task_id']
        task = get_object_or_404(Task, id=task_id)

        user = self.request.user
        # prüfen, ob User Mitglied des Boards ist
        if not task.board.members.filter(id=user.id).exists():
            raise PermissionDenied("You are not a member of this board.")

        # Kommentare zum Task zurückgeben, nach Erstellungsdatum sortiert
        return Comment.objects.filter(task=task).order_by("created_at")

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

class CommentDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/tasks/<task_id>/comments/<comment_id>/
    - nur Author des Kommentars
    - User muss Mitglied (oder Owner) des Boards sein
    - 204 bei Erfolg, sonst 403/404
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        task_id = self.kwargs["task_id"]
        comment_id = self.kwargs["comment_id"]

        # 1) Task holen (404, wenn es ihn nicht gibt)
        task = get_object_or_404(Task, pk=task_id)

        # 2) Mitgliedschaft/Owner prüfen
        is_member = task.board.members.filter(pk=user.id).exists()
        is_owner = task.board.owner_id == user.id
        if not (is_member or is_owner):
            raise PermissionDenied("You must be a board member to delete a comment of this task.")

        # 3) Kommentar holen (404, wenn es ihn (zum Task) nicht gibt)
        comment = get_object_or_404(Comment, pk=comment_id, task=task)

        # 4) Autor prüfen
        if comment.author_id != user.id:
            raise PermissionDenied("Only the author can delete this comment.")

        return comment