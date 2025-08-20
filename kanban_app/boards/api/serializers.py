from typing import TYPE_CHECKING, Any, Dict

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import serializers

from ..models import Board, BoardMember

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as DjangoUser

User = get_user_model()


class BoardListSerializer(serializers.ModelSerializer):
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
    title = serializers.CharField(max_length=200)
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )

    def validate_members(self, value):
        user_ids = list(dict.fromkeys(value))
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
        member_ids = validated_data.get("members", [])

        board = Board.objects.create(title=title, owner=owner)

        if member_ids:
            users = User.objects.filter(id__in=member_ids)
            for u in users:
                try:
                    BoardMember.objects.create(board=board, user=u)
                except IntegrityError:
                    pass

        return board


class UserLiteSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        name = (obj.first_name or "") + (
            " " if obj.first_name and obj.last_name else ""
        ) + (obj.last_name or "")
        return name.strip() or obj.username


class TaskLiteSerializer(serializers.Serializer):
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

    def _user_obj(self, u):
        if not u:
            return None
        name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        return {"id": u.id, "email": u.email, "fullname": name}

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
    owner_id = serializers.IntegerField(read_only=True)
    members = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]

    def get_members(self, obj):
        qs = obj.members.exclude(pk=obj.owner_id)
        return UserLiteSerializer(qs, many=True).data

    def get_tasks(self, obj):
        qs = obj.tasks.all().only("id", "title", "status", "priority")
        return TaskLiteSerializer(qs, many=True).data


class BoardPatchSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, allow_blank=False)
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )

    def validate_members(self, value):
        ids = list(dict.fromkeys(value))
        existing = set(User.objects.filter(id__in=ids).values_list("id", flat=True))
        missing = [i for i in ids if i not in existing]
        if missing:
            raise serializers.ValidationError(f"Unknown user id(s): {missing}")
        return ids


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
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
        members = obj.members.exclude(pk=obj.owner_id).only(
            "id", "email", "first_name", "last_name", "username"
        )
        return [self._user_obj(u) for u in members]
