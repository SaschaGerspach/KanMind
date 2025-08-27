from typing import TYPE_CHECKING, Any, Dict

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Count 
from rest_framework import serializers

from ..models import Board, BoardMember

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as DjangoUser

User = get_user_model()


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing boards with aggregated counters.
    """

    owner_id = serializers.IntegerField(read_only=True)
    member_count = serializers.IntegerField(read_only=True, default=0, required=False)
    ticket_count = serializers.IntegerField(read_only=True, default=0, required=False)
    tasks_to_do_count = serializers.IntegerField(read_only=True, default=0, required=False)
    tasks_high_prio_count = serializers.IntegerField(read_only=True, default=0, required=False)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]


class BoardCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new board with an optional list of members.
    """

    title = serializers.CharField(max_length=200)
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )

    def validate_members(self, value):
        """
        Ensure that all provided member IDs exist in the database.
        """
        user_ids = list(dict.fromkeys(value))  # deduplicate
        existing = set(
            User.objects.filter(id__in=user_ids).values_list("id", flat=True)
        )
        missing = [uid for uid in user_ids if uid not in existing]
        if missing:
            raise serializers.ValidationError(f"Unknown user id(s): {missing}")
        return user_ids

    def create(self, validated_data):
        request = self.context["request"]
        owner = request.user
        title = validated_data["title"]

        board = Board.objects.create(title=title, owner=owner)

        member_ids = validated_data.get("members", [])
        if member_ids:
            self._add_members(board, member_ids)

        return board

    def _add_members(self, board, member_ids):
        """Helper to add members safely to a board."""
        users = User.objects.filter(id__in=member_ids)
        for u in users:
            try:
                BoardMember.objects.create(board=board, user=u)
            except IntegrityError:
                pass


class UserLiteSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for users, including ID, email and full name.
    """

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        """
        Return the full name if available, otherwise username.
        """
        name = (obj.first_name or "") + (
            " " if obj.first_name and obj.last_name else ""
        ) + (obj.last_name or "")
        return name.strip() or obj.username


class TaskLiteSerializer(serializers.Serializer):
    """
    Lightweight serializer for tasks, including basic fields and user references.
    """

    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.SerializerMethodField()
    status = serializers.CharField()
    priority = serializers.CharField()
    assignee = serializers.SerializerMethodField()
    reviewer = serializers.SerializerMethodField()
    due_date = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    def get_description(self, obj):
        return getattr(obj, "description", None)

    def _user_obj(self, user):
        if not user:
            return None
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
        return {"id": user.id, "email": user.email, "fullname": name}

    def get_assignee(self, obj):
        return self._user_obj(getattr(obj, "assignee", None))

    def get_reviewer(self, obj):
        return self._user_obj(getattr(obj, "reviewer", None))

    def get_due_date(self, obj):
        d = getattr(obj, "due_date", None)
        return d.isoformat() if d else None

    def get_comments_count(self, obj):
        return getattr(obj, "comments_count", 0)


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving a board with owner, members, and tasks.
    """

    owner_id = serializers.IntegerField(read_only=True)
    members = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]

    def get_members(self, obj):
        """
        Return members excluding the owner.
        """
        qs = obj.members.exclude(pk=obj.owner_id)
        return UserLiteSerializer(qs, many=True).data

    def get_tasks(self, obj):
        """
        Return lightweight representation of tasks belonging to this board.
        """
        qs = (
            obj.tasks.all()
            .only("id", "title", "status", "priority", "assignee_id", "reviewer_id")
            .select_related("assignee", "reviewer")
            .annotate(comments_count=Count("comments"))
        )
        return TaskLiteSerializer(qs, many=True).data


class BoardPatchSerializer(serializers.Serializer):
    """
    Input serializer for partially updating a board.
    Supports updating title and replacing members.
    """

    title = serializers.CharField(max_length=200, required=False, allow_blank=False)
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )

    def validate_members(self, value):
        """
        Ensure that provided member IDs exist.
        """
        ids = list(dict.fromkeys(value))
        board = self.context.get("board")  
        if board and board.owner_id in ids:
            ids.remove(board.owner_id)
        existing = set(User.objects.filter(id__in=ids).values_list("id", flat=True))
        missing = [i for i in ids if i not in existing]
        if missing:
            raise serializers.ValidationError(f"Unknown user id(s): {missing}")
        return ids


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    """
    Output serializer for board updates.
    Returns board data with owner and members in a lightweight format.
    """

    owner_data = serializers.SerializerMethodField()
    members_data = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members_data"]

    def _fullname(self, u: "DjangoUser") -> str:
        name = f"{u.first_name} {u.last_name}".strip()
        return name or u.username

    def _user_obj(self, u: "DjangoUser") -> Dict[str, Any]:
        return {"id": u.id, "email": u.email, "fullname": self._fullname(u)}

    def get_owner_data(self, obj):
        return self._user_obj(obj.owner)

    def get_members_data(self, obj):
        """
        Return members excluding the owner.
        """
        members = obj.members.all().only(
        "id", "email", "first_name", "last_name", "username"
    )
        return [self._user_obj(u) for u in members]
