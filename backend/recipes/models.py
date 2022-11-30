from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from .validators import validate_is_hex, validate_max_size_text


User = get_user_model()


class Ingredient(models.Model):
    """
    The model to manage ingredients.
    """

    name = models.TextField(
        validators=[validate_max_size_text],
        verbose_name='Название'
    )
    measurement_unit = models.TextField(
        validators=[validate_max_size_text],
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, единица измерения - {self.measurement_unit}'


class Tag(models.Model):
    """
    The model to manage tags. Field 'color' requires
    hex-format for correct serialization.
    """

    name = models.TextField(
        validators=[validate_max_size_text],
        unique=True,
        verbose_name='Название тега'
    )
    color = models.TextField(
        validators=[validate_is_hex],
        default='#ffffff',
        unique=True,
        verbose_name='Цвет'
    )
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    The model to save recipes.
    """

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmountInRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Загрузить фото'
    )
    name = models.TextField(
        validators=[validate_max_size_text],
        verbose_name='Название рецепта'
    )
    text = models.TextField(
        validators=[validate_max_size_text],
        verbose_name='Описание')
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления (в минутах)'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор',
        null=True
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}, автор {self.author}'


class IngredientAmountInRecipe(models.Model):
    """
    The model to make a relationship between
    :model:'recipes.Ingredient' and :model:'recipes.Recipe'
    with additional field 'amount'. Service purposes.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='amount',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='amount',
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в Рецепте'
        verbose_name_plural = 'Ингредиенты в Рецепте'

    def __str__(self):
        return (
            f'Количество {self.ingredient.name} в {self.recipe.name} '
            f'равняется {self.amount}.'
        )


class Favorite(models.Model):
    """
    To save specific relation between both instance of
    :model:'users.User' and :model:'recipes.Recipe'.
    To collect data about user's favourites.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourite',
        null=True,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourite',
        verbose_name='Рецепт',
        null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe', ],
                name='unique_favourite'
            ),
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'У {self.user} рецепт {self.recipe} в избранном.'


class ShoppingCart(models.Model):
    """
    To manage shopping cart - an object to collect
    some recipes and download it.
    """

    user = models.OneToOneField(
        User,
        related_name='customer',
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Пользователь'
    )
    recipe = models.ManyToManyField(
        Recipe,
        related_name='recipes',
        verbose_name='Рецепты'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'Список покупок {self.user}.'
