# Здесь приводятся фильтры queryset Recipe.objects.all()
# по query_params. Наследуем от BaseFilterBackend.
from rest_framework import filters
from rest_framework.exceptions import ValidationError

from recipes.models import Tag



class SpecificAuthorFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'author' field related to
    :model:'recipes.Recipe' instance.
    """

    def filter_queryset(self, request, queryset, view):
        author = request.query_params.get('author')
        if not queryset.filter(author=int(author)).exists():
            raise Exception(
                'Введите корректный id автора.'
            )
        return queryset.filter(author=int(author))


class IsFavouritedFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'is_favorited' field related to
    :model:'recipes.Favorite'.
    """

    def filter_queryset(self, request, queryset, view):
        is_favorited = request.query_params.get('is_favorited')
        if request.user.is_anonymous or is_favorited is None:
            return queryset
        elif (not isinstance(is_favorited, int) or int(is_favorited) != 1):
            raise ValidationError(
                'Чтобы вывести список избранных рецептов'
                ' параметр "is_favorited" должен равняться 1.'
            )
        elif int(is_favorited) == 1:
            return queryset.filter(favourite__user=request.user)


class IsInShoppingCartFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'is_in_shopping_cart' field related to
    :model:'recipes.ShoppingCart'.
    """

    def filter_queryset(self, request, queryset, view):
        is_in_shopping_cart = request.query_params.get(
            'is_in_shopping_cart'
        )
        if is_in_shopping_cart is None or request.user.is_anonymous:
            return queryset
        elif (
            not isinstance(is_in_shopping_cart, int)
            or int(is_in_shopping_cart) != 1
        ):
            raise ValidationError(
                'Чтобы вывести список покупок'
                ' параметр "is_in_shopping_cart" должен равняться 1.'
            )
        elif int(is_in_shopping_cart) == 1:
            return queryset.filter(recipes__user=request.user)


class TagsFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'tags' field related to
    :model:'recipes.Tag'.
    """

    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.get('tags')

        if not Tag.objects.filter(slug=tags).exists():
            raise Exception(
                'Введите корректный slug тега.'
            )
        return queryset.filter(tags__slug=tags)
