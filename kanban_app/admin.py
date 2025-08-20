"""Admin registrations for Boards, Tasks, and Comments."""

from django.contrib import admin

from .boards.models import Board, BoardMember
from .comments.models import Comment
from .tasks.models import Task


# --- Boards -----------------------------------------------------------------


class BoardMemberInline(admin.TabularInline):
    """Inline to manage board members directly on the board admin page."""
    model = BoardMember
    extra = 1
    autocomplete_fields = ["user"]


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin configuration for boards."""
    list_display = ("id", "title", "owner", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "owner__username", "owner__email")
    readonly_fields = ("created_at",)
    inlines = [BoardMemberInline]


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    """Admin configuration for board membership relations."""
    list_display = ("id", "user", "board", "joined_at")
    list_filter = ("joined_at",)
    search_fields = ("user__username", "user__email", "board__title")
    readonly_fields = ("joined_at",)


# --- Tasks & Comments --------------------------------------------------------


class CommentInline(admin.TabularInline):
    """Inline to show/edit comments directly on the task admin page."""
    model = Comment
    extra = 0
    fields = ("author", "content", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    show_change_link = True


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin configuration for tasks."""
    list_display = (
        "id",
        "title",
        "board",
        "status",
        "priority",
        "assignee",
        "reviewer",
        "due_date",
        "created_at",
    )
    list_filter = ("status", "priority", "board", "due_date", "created_at")
    search_fields = (
        "title",
        "description",
        "board__title",
        "assignee__username",
        "assignee__email",
        "reviewer__username",
        "reviewer__email",
    )
    autocomplete_fields = ("board", "assignee", "reviewer", "created_by")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin configuration for comments."""
    list_display = ("id", "task", "author", "created_at", "short_content")
    list_filter = ("created_at", "author", "task__board")
    search_fields = (
        "content",
        "author__username",
        "author__email",
        "task__title",
        "task__board__title",
    )
    autocomplete_fields = ("task", "author")
    readonly_fields = ("created_at",)

    def short_content(self, obj):
        """Compact preview of the comment body for list display."""
        text = obj.content or ""
        return (text[:60] + "…") if len(text) > 60 else text

    short_content.short_description = "content"
