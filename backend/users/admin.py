from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscription
from recipes.models import (
    Ingredient, Tag, Recipe, IngredientAmountInRecipe,
    Favorite, ShoppingCart
)


class IngredientRecipeInLine(admin.TabularInline):
    model = IngredientAmountInRecipe
    raw_id_fields = ['ingredient',]
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    """
    To filter recipes against author, name and tags.
    """
    readonly_fields = ('favorite',)
    list_filter = ('author', 'name', 'tags',)
    inlines = (IngredientRecipeInLine,)

    def favorite(self, obj):
        return obj.favourite.count()


class UserAdminExtended(UserAdmin):
    """
    To filter users against email and username.
    """

    list_filter = UserAdmin.list_filter + ('email', 'username',)


class IngredientAdmin(admin.ModelAdmin):
    """
    To filter recipes against author, name and tags.
    """

    list_filter = ('name',)


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientAmountInRecipe)
admin.site.register(Favorite)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Subscription)
admin.site.register(ShoppingCart)
admin.site.register(Tag)
admin.site.register(User, UserAdminExtended)
