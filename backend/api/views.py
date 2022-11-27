from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase

from .filters import (
    SpecificAuthorFilterBackend,
    IsFavouritedFilterBackend,
    IsInShoppingCartFilterBackend,
    TagsFilterBackend,
)
from .serializers import (
    UserSerializer,
    UserSignUpSerializer,
    ChangePasswordSerializer,
    FoodgramTokenObtainSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeMinifiedSerializer,
    UserWithRecipeMinifiedSerializer
)
from .paginations import PageNumberLimitPagination
from .permissions import (
    AllowAnyIfNotObject,
    IsAuthorOrReadOnly,
    IsAuthenticatedOrOwner,
)
from users.models import Subscription
from recipes.models import Ingredient, Tag, Recipe, ShoppingCart, Favorite


User = get_user_model()


class CreateRetrieveListViewSet(mixins.CreateModelMixin,
                                mixins.RetrieveModelMixin,
                                mixins.ListModelMixin,
                                viewsets.GenericViewSet):
    """
    Generic viewset to create, retrieve and get list of
    :model:'users.User' instances."""

    pass


class UserViewSet(CreateRetrieveListViewSet):
    """
    A viewset to provide 'create', 'list' and 'retrieve'
    actions with :model:'users.User.'
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberLimitPagination
    permission_classes = (AllowAnyIfNotObject,)

    def create(self, request):

        # Создаем юзера, хешируем пароль.
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attrs = serializer.data
        initial_data = {
            'username': attrs['username'],
            'email': attrs['email'],
            'first_name': attrs['first_name'],
            'last_name': attrs['last_name'],
        }
        user = User(**initial_data)
        user.set_password(serializer.data.get('password'))
        user.save()

        # Возвращаем поле 'id' в сериализацию.
        instance = get_object_or_404(User, username=user.username)
        serializer = UserSignUpSerializer(instance)

        return Response(serializer.data)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request):
        user = get_object_or_404(User, username=request.user.username)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        user = get_object_or_404(User, username=request.user.username)
        serializer = ChangePasswordSerializer(data=request.data)

        if not user.check_password(request.data['current_password']):
            raise ValidationError(
                'Введен неверный пароль от аккаунта. Попробуйте снова.'
            )

        if serializer.is_valid():
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk):
        """
        To manage :model:'users.Subscription' instances.
        """
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя.')

        subscription = Subscription.objects.filter(user=user, author=author)

        if self.request.method == 'POST':
            if subscription.exists():
                raise ValidationError(f'Подписка на {author} уже существует.')
            Subscription(user=user, author=author).save()
            serializer = UserWithRecipeMinifiedSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data)

        elif self.request.method == 'DELETE':
            if not subscription.exists():
                raise ValidationError(f'Подписки на {author} не существует.')
            Subscription.objects.get(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'': f'{self.request.method}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user_subscriptions = User.objects.filter(
            subscribing__user=self.request.user
        )
        page = self.paginate_queryset(user_subscriptions)

        if page is not None:
            serializer = UserWithRecipeMinifiedSerializer(
                page,
                context={'request': request},
                many=True
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipeMinifiedSerializer(
            page,
            context={'request': request},
            many=True
        )
        return Response(serializer.data)


class LogoutView(APIView):
    """
    To kill token with blacklist.
    """

    def post(self, request):

        try:
            RefreshToken(str(request.auth)).blacklist()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class TokenObtainFoodgramView(TokenViewBase):
    """
    To give a user jwt-token. Fields: 'email' & 'password'.
    """

    permission_classes = (AllowAny,)
    serializer_class = FoodgramTokenObtainSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset only allows to present
    instances of :model:'recipes.Tag'.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    To get :model:'recipes.Ingredient' instances.
    To search by name use 'search' query param.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    This viewset to manage endpoint recipes/,
    including all the CRUD-operations,
    realated to :model:'recipes.Recipe'.
    """

    queryset = Recipe.objects.all().order_by('-pub_date')
    serializer_class = RecipeSerializer
    pagination_class = PageNumberLimitPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (
        SpecificAuthorFilterBackend,
        IsFavouritedFilterBackend,
        IsInShoppingCartFilterBackend,
        TagsFilterBackend,
    )
    filterset_fields = (
        'author',
        'is_favorited',
        'is_in_shopping_cart',
        'tags',
    )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticatedOrOwner,)
    )
    def favorite(self, request, pk=None):

        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        query = Favorite.objects.filter(user=user, recipe=recipe)

        if self.request.method == 'POST':
            if query.exists():
                raise ValidationError(f'{recipe} уже в избранном.')
            Favorite(user=user, recipe=recipe).save()
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data)
        elif self.request.method == 'DELETE':
            if not query.exists():
                raise ValidationError(f'{recipe} отсутствует в избранном.')
            Favorite.objects.get(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'': f'{self.request.method}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticatedOrOwner,)
    )
    def shopping_cart(self, request, pk=None):

        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart = ShoppingCart.objects.get_or_create(user=user)
        query = ShoppingCart.objects.filter(user=user, recipe=recipe)

        if self.request.method == 'POST':
            if query.exists():
                raise ValidationError(f'{recipe} уже в списке покупок.')
            shopping_cart[0].recipe.add(recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data)
        elif self.request.method == 'DELETE':
            if not query.exists():
                raise ValidationError(
                    f'{recipe} отсутствует в Вашем списке покупок.'
                )
            shopping_cart[0].recipe.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):

        user = request.user
        try:
            shopping_recipes = Recipe.objects.filter(
                recipes__user=user
            )
            ingredients = shopping_recipes.values_list(
                'amount__ingredient__name',
                'amount__ingredient__measurement_unit'
            ).order_by('amount__ingredient__name')
            total = ingredients.annotate(
                amount=Sum('amount__amount')
            )

            shopping_cart = 'Список покупок:'
            for ingr in total:
                shopping_cart += f'\n{ingr[0]}: {ingr[2]} {ingr[1]}'
            return HttpResponse(
                shopping_cart,
                content_type='text/plain'
            )
        except Exception:
            raise Exception('Список покупок пуст.')
