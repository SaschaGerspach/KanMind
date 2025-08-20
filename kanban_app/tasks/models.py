from django.contrib.auth import get_user_model
from django.db import models

from ..boards.models import Board

User = get_user_model()


class Task(models.Model):
    """
    Represents a single task within a board.
    Each task belongs to a board and may have an assignee, a reviewer,
    and optional metadata like due date and priority.
    """

    # Allowed priority levels
    PRIORITY = (
        ("low", "low"),
        ("medium", "medium"),
        ("high", "high"),
    )

    # Allowed workflow status values
    STATUS = (
        ("to-do", "to-do"),
        ("in-progress", "in-progress"),
        ("review", "review"),
        ("done", "done"),
    )

    # The board this task belongs to (mandatory)
    board = models.ForeignKey(
        Board,
        related_name="tasks",
        on_delete=models.CASCADE,
    )

    # Task details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Workflow attributes
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="to-do",
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY,
        default="medium",
    )

    # User assignments
    assignee = models.ForeignKey(
        User,
        related_name="assigned_tasks",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # Assignee may be deleted without removing the task
    )
    reviewer = models.ForeignKey(
        User,
        related_name="reviewing_tasks",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # Reviewer may be deleted without removing the task
    )

    # Optional metadata
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # The user who originally created the task
    created_by = models.ForeignKey(
        User,
        related_name="created_tasks",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # Creator may be deleted without removing the task
    )

    def __str__(self):
        """
        String representation of the task,
        by default the task's title is shown.
        """
        return self.title
