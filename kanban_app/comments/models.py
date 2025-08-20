from django.conf import settings
from django.db import models

from ..tasks.models import Task


class Comment(models.Model):
    """
    Model representing a comment on a task.
    Each comment is linked to a task and an author (user).
    """

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="The task this comment belongs to.",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The user who wrote this comment.",
    )
    content = models.TextField(
        help_text="The actual text content of the comment."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the comment was created."
    )

    def __str__(self):
        """
        Returns a readable string representation of the comment.
        Example: 'Comment#5 by user1 on Task#10'
        """
        return f"Comment#{self.pk} by {self.author} on Task#{self.task_id}"
