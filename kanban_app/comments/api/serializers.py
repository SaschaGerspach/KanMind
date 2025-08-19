from rest_framework import serializers
from kanban_app.comments.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]

class CommentCreateSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
        read_only_fields = ["id", "created_at", "author"]

    def get_author(self, obj):
        u = obj.author
        full = f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}".strip()
        return full or u.username
