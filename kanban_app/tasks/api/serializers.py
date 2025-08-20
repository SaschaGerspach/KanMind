from django.contrib.auth import get_user_model
from rest_framework import serializers

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

        if assignee and not board.members.filter(pk=assignee.id).exists():
            raise serializers.ValidationError(
                "Assignee must be a member of the board."
            )

        if reviewer and not board.members.filter(pk=reviewer.id).exists():
            raise serializers.ValidationError(
                "Reviewer must be a member of the board."
            )

        return attrs


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
        ]

    def validate(self, data):
        task = self.instance

        if "board" in data and data["board"] != task.board:
            raise serializers.ValidationError(
                "The board ID cannot be changed."
            )

        if (
            "assignee" in data
            and data["assignee"]
            and not task.board.members.filter(id=data["assignee"].id).exists()
        ):
            raise serializers.ValidationError(
                "The assignee must be a member of the board."
            )

        if (
            "reviewer" in data
            and data["reviewer"]
            and not task.board.members.filter(id=data["reviewer"].id).exists()
        ):
            raise serializers.ValidationError(
                "The reviewer must be a member of the board."
            )

        return data
