"""Custom permission classes shared across boards, tasks, and comments.
"""
from typing import Any, Optional

from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request

from .boards.models import Board
from .tasks.models import Task


def _resolve_board(obj: Any) -> Optional[Board]:
    """Extract a Board instance from `obj` (Board itself or an object with .board)."""
    if hasattr(obj, "board") and isinstance(obj.board, Board):
        return obj.board
    if isinstance(obj, Board):
        return obj
    return None


class IsAuthenticatedAndReadOnly(BasePermission):
    """Allow GET/HEAD/OPTIONS for authenticated users only."""
    def has_permission(self, request: Request, view) -> bool:
        return request.user.is_authenticated and request.method in SAFE_METHODS


class IsBoardOwner(BasePermission):
    """Allow access only if the request user is the board owner."""
    def has_object_permission(self, request: Request, view, obj: Any) -> bool:
        board = _resolve_board(obj)
        return bool(
            request.user.is_authenticated
            and board
            and board.owner_id == request.user.id
        )


class IsBoardMember(BasePermission):
    """Allow access only if the request user is a member of the board."""
    def has_object_permission(self, request: Request, view, obj: Any) -> bool:
        user = request.user
        board = _resolve_board(obj)
        return bool(
            user.is_authenticated
            and board
            and board.members.filter(pk=user.id).exists()
        )


class IsBoardOwnerOrMember(BasePermission):
    """Allow access if the request user is board owner OR member."""
    def has_object_permission(self, request: Request, view, obj: Any) -> bool:
        user = request.user
        board = _resolve_board(obj)
        if not (user.is_authenticated and board):
            return False
        return (
            board.owner_id == user.id
            or board.members.filter(pk=user.id).exists()
        )


class CanCreateTaskOnBoard(BasePermission):
    """
    Pre-object permission for POST /tasks/:
    user must be the target board's owner OR a member.
    """
    message = "You must be a member or the owner of the board to create a task."

    def has_permission(self, request: Request, view) -> bool:
        if request.method != "POST":
            return True
        if not request.user.is_authenticated:
            return False
        board_id = request.data.get("board")
        if not board_id:
            return False
        board = get_object_or_404(Board, pk=board_id)
        return (
            board.owner_id == request.user.id
            or board.members.filter(pk=request.user.id).exists()
        )


class CanDeleteTaskIfCreatorOrBoardOwner(BasePermission):
    """For DELETE on Task: only the task creator or the board owner."""
    def has_object_permission(self, request: Request, view, obj: Any) -> bool:
        if request.method != "DELETE":
            return True
        user = request.user
        board = _resolve_board(obj)
        return bool(
            user.is_authenticated
            and board
            and (
                getattr(obj, "created_by_id", None) == user.id
                or board.owner_id == user.id
            )
        )


class CanAccessTaskBoardFromURL(BasePermission):
    """
    Pre-object permission using task_id from URL:
    allow if the user is the board owner OR a board member.
    Intended for list/create/delete of comments under a task.
    """
    message = "You must be an owner or member of this board."

    def has_permission(self, request: Request, view) -> bool:
        task_id = view.kwargs.get("task_id")
        if not task_id or not request.user.is_authenticated:
            return False

        task = get_object_or_404(Task, pk=task_id)
        board = task.board
        user = request.user
        return (
            board.owner_id == user.id
            or board.members.filter(pk=user.id).exists()
        )


class IsCommentAuthor(BasePermission):
    """
    Object-level permission: only the comment's author may delete it.
    (Board access is checked separately.)
    """
    message = "Only the author can delete this comment."

    def has_object_permission(self, request: Request, view, obj: Any) -> bool:
        if request.method != "DELETE":
            return True
        return (
            request.user.is_authenticated
            and getattr(obj, "author_id", None) == request.user.id
        )
