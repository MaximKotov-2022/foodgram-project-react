from api.serializers import (RecipeCreateSerializer, RecipeSerializer,
                             TagSerializer, UserCreateSerializer,
                             UserGetSerializer)
from djoser.views import UserViewSet
from recipes.models import Recipe, Tag
from rest_framework.viewsets import ModelViewSet

from .models import User
from .permissions import IsCurrentOrAdminOrReadOnly


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    permission_classes = (IsCurrentOrAdminOrReadOnly,)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            'recipeingredient_set__ingredient', 'tags'
        ).all()
        return recipes

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
