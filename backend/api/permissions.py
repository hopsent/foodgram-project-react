from rest_framework.permissions import SAFE_METHODS, BasePermission


class AllowAnyIfNotObject(BasePermission):
    """
    To grant access for anyone except object-level access.
    Should be authenticated user to access the object.
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
        )
