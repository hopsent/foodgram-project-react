# Здесь приводятся фильтры queryset Recipe.objects.all()
# по query_params. Наследуем от BaseFilterBackend.
from rest_framework import filters
from rest_framework.exceptions import ValidationError

from users.models import User


class SpecificAuthorFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'author' field related to
    :model:'recipes.Recipe' instance.
    """

    def filter_queryset(self, request, queryset, view):
        author = request.query_params.get('author')
        if author is None:
            return queryset
        elif not User.objects.filter(id=int(author)).exists():
            raise ValidationError(
                'Введите корректный id автора.'
            )
        return queryset.filter(author=int(author))


class IsFavouritedFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'is_favorited' field related to
    :model:'recipes.Favorite'. Expected values: 0 or 1.
    """

    def filter_queryset(self, request, queryset, view):
        is_favorited = request.query_params.get('is_favorited')
        if (
            is_favorited is None
            or request.user.is_anonymous
            or int(is_favorited) == 0
        ):
            return queryset
        return queryset.filter(favourite__user=request.user)


class IsInShoppingCartFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'is_in_shopping_cart' field related to
    :model:'recipes.ShoppingCart'. Expected values: 0 or 1.
    """

    def filter_queryset(self, request, queryset, view):
        is_in_shopping_cart = request.query_params.get(
            'is_in_shopping_cart'
        )
        if (
            is_in_shopping_cart is None
            or request.user.is_anonymous
            or int(is_in_shopping_cart) == 0
        ):
            return queryset
        return queryset.filter(recipes__user=request.user)


class TagsFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'tags' field related to
    :model:'recipes.Tag'.
    """

    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.get('tags')
        if tags is None:
            return queryset
        return queryset.filter(tags__slug=tags)


class IngredientNameFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        name = request.query_params.get('name').lower()
        return queryset.filter(
            name__startswith=name
        )
