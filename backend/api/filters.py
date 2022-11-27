# Здесь приводятся фильтры queryset Recipe.objects.all()
# по query_params. Наследуем от BaseFilterBackend.
from rest_framework import filters


class SpecificAuthorFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'author' field related to
    :model:'recipes.Recipe' instance.
    """

    def filter_queryset(self, request, queryset, view):
        author = request.query_params.get('author')
        if author is None:
            return queryset
        try:
            return queryset.filter(author=int(author))
        except Exception:
            raise Exception(
                'Введите корректное значение параметра запроса'
                ' author - число.'
            )


class IsFavouritedFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'is_favorited' field related to
    :model:'recipes.Favorite'.
    """

    def filter_queryset(self, request, queryset, view):
        is_favorited = request.query_params.get('is_favorited')
        if request.user.is_anonymous or is_favorited is None:
            return queryset
        try:
            if int(is_favorited) == 1:
                return queryset.filter(
                    favourite__user=request.user
                )
        except Exception:
            raise Exception(
                'Введите корректное значение параметра запроса'
                ' is_favorite - число.'
            )


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
        try:
            if int(is_in_shopping_cart) == 1:
                return queryset.filter(
                    recipes__user=request.user
                )
        except Exception:
            raise Exception(
                'Введите корректное значение параметра запроса'
                ' is_in_shopping_cart - число.'
            )


class TagsFilterBackend(filters.BaseFilterBackend):
    """
    To filter queryset with 'tags' field related to
    :model:'recipes.Tag'.
    """

    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.get('tags')
        if tags is None:
            return queryset
        try:
            return queryset.filter(tags__slug=tags)
        except Exception:
            raise Exception(
                'Введите корректное значение параметра'
                ' запроса tags - должно быть значение поля slug'
                ' у объекта модели Tag.'
            )
