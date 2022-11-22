from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import (TokenObtainFoodgramView,
    LogoutView, UserViewSet, TagViewSet, IngredientViewSet,
    RecipeViewSet,
)


router = DefaultRouter()
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('users', UserViewSet)


urlpatterns = [
    path('auth/token/login/', TokenObtainFoodgramView.as_view(), name='token_obtain'),
    path('auth/token/logout/', LogoutView.as_view(), name='token_logout'),
    path('', include(router.urls)),
]
