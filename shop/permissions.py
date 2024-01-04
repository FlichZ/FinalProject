from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Пользователи с правами сотрудника имеют доступ к изменению, остальные - только к просмотру.
    """

    def has_permission(self, request, view):
        # Разрешить GET, HEAD, OPTIONS запросы для всех пользователей
        if request.method in permissions.SAFE_METHODS:
            return True
        # Разрешить изменение только для сотрудников
        return request.user and request.user.is_staff
