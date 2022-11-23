from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import PasswordField


from recipes.models import Ingredient, Tag, Recipe, IngredientAmountInRecipe
from users.models import User
from .fields import Hex2NameColor, Base64ImageField



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

    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'color', 'name', 'slug',)
        # Выключаем возможность запроса к серверу по полям ниже,
        # как это требуется для сериализации рецептов, где этот
        # сериализатор выступает вложенным.
        read_only_fields = ('name', 'color','slug',)

    def validate_id(self, value):
        get_object_or_404(Tag, id=value)
        return value

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
    :model:'recipes.IngredientAmountInRecipe'.
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
    Part of many-to-many relation.
    For nesting purposes only.
    """

    id = serializers.ReadOnlyField(
        source='ingredient.amount.id'
    )
    amount = serializers.ReadOnlyField(
        source='ingredient.amount.measurement_unit'
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'amount', 'name', 'measurement_unit',)


class RecipeSerializer(serializers.ModelSerializer):
    """
    """

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
        )

#    def to_representation(self, instance):
#
#        output = {}
#        print(dir(instance))
#        print(instance.__dict__)
#        for attribute_name in dir(instance):

#            attribute = getattr(instance, attribute_name)
#            if attribute_name.startswith('_'):
#                # Ignore private attributes.
#                pass
#            elif hasattr(attribute, '__call__'):
#                # Ignore methods and other callables.
#                pass
#            elif isinstance(attribute, (str, int, bool, float, type(None))):
#                # Primitive types can be passed through unmodified.
#                output[attribute_name] = attribute
#            elif isinstance(attribute, Ingredient):
#                # Recursively deal with items in dictionaries.
#                output[attribute_name] = IngredientShowSerializer(attribute).data
#            elif isinstance(attribute, Tag):
#                # Recursively deal with items in dictionaries.
#                output[attribute_name] = TagSerializer(attribute).data
#            else:
#                # Force anything else to its string representation.
#                output[attribute_name] = str(attribute)


#       return output
    def to_representation(self, instance):
        response = super().to_representation(instance)
        print('dot')
        response['ingredients'] = IngredientShowSerializer(instance.ingredients).data
        response['tags'] = IngredientShowSerializer(instance.tags).data
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
        for dct in ingredients:
            ingredient = dct['ingredient']
            #ingredient = get_object_or_404(Ingredient, id=dct.get('id'))
            IngredientAmountInRecipe.objects.get_or_create(
                recipe=recipe,
                ingredient=ingredient,
                amount=dct.get('amount')
            )

        # Присоединяем к рецепту теги.
        list_of_tags = []
        for tag in tags:
            new_tag = get_object_or_404(Tag, id=tag.id)
            list_of_tags.append(new_tag)
        recipe.tags.set(list_of_tags)

        return recipe

  #  def update(self, instance, validated_data):

 #       instance.name = validated_data.name
 #      instance.image = validated_data.image
 #       instance.text = validated_data.text
 #       instance.cooking_time = validated_data.cooking_time

 #       ingredients = validated_data.pop('ingredients')
 #       tags = validated_data.pop('tags')

#        new_ingredients = []
#        for ingredient in ingredients:
#            new_ingredient = get_object_or_404(
#                Ingredient,
#                ingredient=ingredient.id,
#            )
#            new_ingredients.append(new_ingredient)
#            IngredientAmountInRecipe.objects.create(

#            )
#            validated_data.ingredients.amount
      #      new_ingredient.amount.amount = 

#        instance.ingredients.set(new_ingredients)

#        instance.save()
#        return instance


class RecipeMinifiedSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
