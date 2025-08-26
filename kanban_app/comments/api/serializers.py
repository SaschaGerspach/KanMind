from rest_framework import serializers

from kanban_app.comments.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for reading comment data.
    Includes the author's full name as a read-only field.
    """
    author = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new comments.
    - Author is automatically derived from the request user (read-only here).
    - 'id' and 'created_at' are also read-only.
    """
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
        read_only_fields = ["id", "created_at", "author"]

    def get_author(self, obj):
        """
        Returns the author's full name (first + last).
        If no full name exists, fallback to username.
        """
        user = obj.author
        full = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
        return full or user.username
