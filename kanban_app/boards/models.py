from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """
    Represents a project board which contains tasks and members.
    Each board has an owner (creator) and can include multiple members.
    """

    title = models.CharField(max_length=200)
    owner = models.ForeignKey(
        User,
        related_name="owned_boards",
        on_delete=models.CASCADE,
        help_text="User who created and owns the board.",
    )
    members = models.ManyToManyField(
        User,
        through="BoardMember",
        related_name="boards",
        blank=True,
        help_text="Users who are members of the board (via BoardMember relation).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the board was created."
    )

    def __str__(self):
        return self.title


class BoardMember(models.Model):
    """
    Intermediate model to represent the membership of a user in a board.
    Ensures that each user can only be added once per board.
    """

    board = models.ForeignKey(
        Board,
        related_name="board_memberships",
        on_delete=models.CASCADE,
        help_text="The board this membership belongs to."
    )
    user = models.ForeignKey(
        User,
        related_name="board_memberships",
        on_delete=models.CASCADE,
        help_text="The user who is a member of the board."
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the user joined the board."
    )

    class Meta:
        unique_together = ("board", "user")
        verbose_name = "Board Member"
        verbose_name_plural = "Board Members"

    def __str__(self):
        return f"{self.user.username} in {self.board.title}"
