from rest_framework.permissions import BasePermission

class CanUpdateTaskOnBoard(BasePermission):
    """
    Darf Task ändern, wenn User Board-Owner oder Board-Mitglied ist.
    Wirken auf PATCH/PUT/DELETE (objektbezogen).
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        board = obj.board
        return (
            user.is_authenticated
            and (board.owner_id == user.id or board.members.filter(pk=user.id).exists())
        )