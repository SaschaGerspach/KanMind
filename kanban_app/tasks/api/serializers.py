from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Task

User = get_user_model()


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
        ]

    def validate_status(self, value):
        allowed = ["to-do", "in-progress", "review", "done"]
        if value not in allowed:
            raise serializers.ValidationError("Invalid status value.")
        return value

    def validate_priority(self, value):
        allowed = ["low", "medium", "high"]
        if value not in allowed:
            raise serializers.ValidationError("Invalid priority value.")
        return value

    def validate(self, attrs):
        board = attrs.get("board")
        assignee = attrs.get("assignee")
        reviewer = attrs.get("reviewer")

        # Assignee muss Mitglied im Board sein
        if assignee and not board.members.filter(pk=assignee.id).exists():
            raise serializers.ValidationError("Assignee must be a member of the board.")

        # Reviewer muss Mitglied im Board sein
        if reviewer and not board.members.filter(pk=reviewer.id).exists():
            raise serializers.ValidationError("Reviewer must be a member of the board.")

        return attrs
