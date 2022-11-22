from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscription
from recipes.models import (
    Ingredient, Tag, Recipe, IngredientAmountInRecipe
)

class IngredientRecipeInLine(admin.TabularInline):
    model = IngredientAmountInRecipe
    raw_id_fields = ['ingredient',]
    # extra = 1
    min_num = 1


admin.site.register(Ingredient)
admin.site.register(IngredientAmountInRecipe)
admin.site.register(Recipe, inlines = (IngredientRecipeInLine,))
admin.site.register(Subscription)
admin.site.register(Tag)
admin.site.register(User, UserAdmin)