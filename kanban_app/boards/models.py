from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    title = models.CharField(max_length=200)
    owner = models.ForeignKey(
        User,
        related_name="owned_boards",
        on_delete=models.CASCADE,
    )
    members = models.ManyToManyField(
        User,
        through="BoardMember",
        related_name="boards",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class BoardMember(models.Model):
    board = models.ForeignKey(
        Board,
        related_name="board_memberships",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        related_name="board_memberships",
        on_delete=models.CASCADE,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("board", "user")
