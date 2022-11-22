from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


User = get_user_model()


class Ingredient(models.Model):
    """
    The model to manage ingredients.
    """

    name = models.CharField(max_length=50, verbose_name='Название')
    measurement_unit = models.CharField(max_length=16)
  
    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    The model to manage tags. Field 'color' requires
    hex-format for correct serialization.
    """

    name = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=15, unique=True)
    slug = models.SlugField(unique=True)

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
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Загрузить фото'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    text = models.TextField(verbose_name='Описание')
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

    def __str__(self):
        return self.name


class IngredientAmountInRecipe(models.Model):
    """
    The model to make a relationship between
    :model:'recipes.Ingredient' and :model:'recipes.Recipe'
    with additional field 'amount'. Service purposes.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='amount'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='amount'
    )
    amount = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return (
            f'Количество {self.ingredient.name} в {self.recipe.name} '
            f'равняется {self.amount}.'
        )
