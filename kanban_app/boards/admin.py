from django.contrib import admin
from .models import Board, BoardMember

class BoardMemberInline(admin.TabularInline):
    model = BoardMember
    extra = 1
    autocomplete_fields = ["user"]

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "owner__username", "owner__email")
    readonly_fields = ("created_at",)
    inlines = [BoardMemberInline]

@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "board", "user", "joined_at")
    list_filter = ("joined_at",)
    search_fields = ("board__title", "user__username", "user__email")
    readonly_fields = ("joined_at",)