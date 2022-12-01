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


class IsAuthorOrReadOnly(BasePermission):
    """
    To grant author access the recipe and to grant general access
    recipes if method is safe or user is authenticated.
    """

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or obj.author == request.user)


class IsAuthenticatedOrOwner(BasePermission):
    """
    To grant customer access the shopping cart and favorite
    or general access to create shopping cart and favorite
    if user is authenticated.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user
