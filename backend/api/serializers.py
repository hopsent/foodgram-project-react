from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import PasswordField


from recipes.models import (
    Ingredient, Tag, Recipe,
    IngredientAmountInRecipe,
    ShoppingCart,
)
from .fields import Base64ImageField
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Base serializer related to :model:'users.User'.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        read_only_fields = ('id', 'is_subscribed',)

    def get_is_subscribed(self, obj):

        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.subscribing.filter(user=user).exists()


class UserSignUpSerializer(serializers.ModelSerializer):
    """
    To serilize sign up data
    and to exclude 'is_subscribe'-field from the Response.
    """

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint
    api/users/set_password.
    """

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    # Проверяем новый пароль дефолотными средствами.
    def validate_new_password(self, value):
        validate_password(value)
        return value


class FoodgramTokenObtainSerializer(serializers.Serializer):
    """
    Serializer to provide users with jwt-tokens with endpoint
    api/auth/token/login/.
    Fields: 'email', 'password'.
    """
    email = serializers.CharField()
    password = PasswordField()

    def validate(self, attrs):
        # Проверяем наличие юзера в базе.
        user = get_object_or_404(User, email=attrs['email'])
        if user is None:
            raise ValidationError(
                'Пользователя с таким email не существует.'
            )

        # Проверяем корректность введенного пароля.
        password = attrs['password']
        if not user.check_password(password):
            raise ValidationError('Введен неверный пароль.')

        # Создаем словарь data и прописываем в него токен.
        data = {}
        data['auth_token'] = str(RefreshToken.for_user(user))

        return data


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer related to :model:'recipes.Tag'.
    """

    class Meta:
        model = Tag
        fields = ('id', 'color', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer related to :model:'recipes.Ingredient'.
    """

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountSerializer(serializers.ModelSerializer):
    """
    To serialize the through model as part of many-to-many relation -
    :model:'recipes.IngredientAmountInRecipe'. Usage: POST-request with
    ingredient.id and amount of Ingredient() related to certain Recipe().
    For nesting purposes only.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = IngredientAmountInRecipe
        fields = ('id', 'amount',)


class IngredientShowSerializer(serializers.ModelSerializer):
    """
    Part of many-to-many relation. Operated in to_representation
    of RecipeSerializer to present 'ingredients' field of
    :model:'recipes.Recipe'. For nesting purposes only.
    """

    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmountInRecipe
        fields = ('id', 'amount', 'name', 'measurement_unit',)


class RecipeSerializer(serializers.ModelSerializer):
    """
    """

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField()
    author = UserSerializer(allow_null=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):

        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.favourite.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):

        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.recipes.filter(user=user).exists()

    def to_representation(self, instance):
        # Переопределяем, чтобы презентовать поля ManyToMany,
        # относящиеся к Recipe()
        self.fields.pop('ingredients', 'tags')
        response = super().to_representation(instance)
        response['ingredients'] = IngredientShowSerializer(
            instance.amount.all(),
            many=True
        ).data
        response['tags'] = TagSerializer(instance.tags.all(), many=True).data
        return response

    def create(self, validated_data):
        # Переопределяем метод create для реализации
        # many-to-many связи между объектами.
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        # Устанавливаем на рецепт ингредиенты и их количество.
        lst_of_ingr = []
        for dct in ingredients:
            ingredient = dct.get('ingredient')
            lst_of_ingr.append(
                IngredientAmountInRecipe(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=dct.get('amount')
                )
            )
        IngredientAmountInRecipe.objects.bulk_create(lst_of_ingr)

        # Присоединяем к рецепту теги.
        list_of_tags = []
        for tag in tags:
            new_tag = get_object_or_404(Tag, id=tag.id)
            list_of_tags.append(new_tag)
        recipe.tags.set(list_of_tags)

        return recipe

    def update(self, instance, validated_data):

        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )

        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        lst_of_ingr = []
        for dct in ingredients:
            ingredient = dct.get('ingredient')
            lst_of_ingr.append(
                IngredientAmountInRecipe(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=dct.get('amount')
                )
            )
        IngredientAmountInRecipe.objects.bulk_update(
            instance.ingredients,
            lst_of_ingr
        )

        list_of_tags = []
        for tag in tags:
            new_tag = get_object_or_404(Tag, id=tag.id)
            list_of_tags.append(new_tag)
        instance.tags.set(list_of_tags)

        return instance


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    To provide a truncated representation of
    :model:'recipes.Recipe' instance.
    """

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class UserWithRecipeMinifiedSerializer(UserSerializer):
    """
    To provide combined serializer with both UserSerializer fields
    and RecipeMinifiedSerializer fields with nested representation.
    """

    recipes = RecipeMinifiedSerializer(many=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count',)

    def to_representation(self, instance):
        # Если автор не опубликовал рецепт, возвращаем дефолтное значение,
        # чтобы избежать KeyError.
        self.fields.pop('recipes', 'recipes')
        response = super().to_representation(instance)
        # Определяем, если поступил параметр - количество рецептов на странице.
        # Если параметр не задан, количество рецептов лимитируется 5.
        lmt = self.context['request'].query_params.get('recipes_limit') or 5
        response['recipes'] = RecipeMinifiedSerializer(
            instance.recipe.all().order_by('-pub_date')[:int(lmt)],
            many=True
        ).data

        return response

    # Считаем количество рецептов автора.
    def get_recipes_count(self, obj):
        return obj.recipe.all().count()
