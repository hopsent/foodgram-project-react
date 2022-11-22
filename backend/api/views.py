from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase

from .serializers import (
    UserSerializer,
    UserSignUpSerializer,
    ChangePasswordSerializer,
    FoodgramTokenObtainSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
)
from .paginations import PageNumberLimitPagination
from .permissions import AllowAnyIfNotObject
from users.models import User, Subscription
from recipes.models import Ingredient, Tag, Recipe


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

    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        user = get_object_or_404(User, username=request.user.username)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = get_object_or_404(User, username=request.user.username)
        serializer = ChangePasswordSerializer(data=request.data)

        if not user.check_password(request.data['current_password']):
            raise ValidationError(
                f'Введен неверный пароль от аккаунта. Попробуйте снова.'
            )

        if serializer.is_valid():
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response(
                {"message": "Пароль изменен успешно"},
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
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
                raise ValidationError('Подписка на этого автора уже существует.')
            Subscription(user=user, author=author).save()
            serializer = UserSerializer(author, context={'request': request})
            return Response(serializer.data)

        elif self.request.method == 'DELETE':
            if not subscription.exists():
                raise ValidationError('Подписки на этого автора не существует.')
            Subscription.objects.get(user=user, author=author).delete()
            return Response(
                {'message': 'Успешная отписка.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"": f'{self.request.method}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user_subscriptions = User.objects.filter(
            subscribing__user=self.request.user
        )
        page = self.paginate_queryset(user_subscriptions)

        if page is not None:
            serializer = UserSerializer(
                page,
                context={'request': request},
                many=True
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(
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

            return Response(
                {"message": "Токен добавлен черный список"},
                status=status.HTTP_205_RESET_CONTENT
            )

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
    
    """

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageNumberLimitPagination
