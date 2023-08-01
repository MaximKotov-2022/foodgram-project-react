from api.serializers import (FavoriteSerializer, FollowSerializer,
                             IngredientGetSerializer, RecipeCreateSerializer,
                             RecipeSerializer, SubscriptionsSerializer,
                             TagSerializer, UserCreateSerializer,
                             UserGetSerializer)
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import Favorite, Ingredient, Recipe, Tag
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import Follow, User
from .permissions import IsCurrentOrAdminOrReadOnly


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    permission_classes = (IsCurrentOrAdminOrReadOnly,)


class SubscriptionsViewSet(CustomUserViewSet):
    queryset = User.objects.all()
    serializer_class = SubscriptionsSerializer
    permission_classes = (IsAuthenticated,)

    @action(methods=['get'], detail=True, url_path='subscriptions', permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=request.user).all()
        paginator = PageNumberPagination()
        paginated_subscriptions = paginator.paginate_queryset(subscriptions, request)
        serializer = self.get_serializer(paginated_subscriptions, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        if request.method == 'POST':
            author = get_object_or_404(User, id=id)
            if author == request.user:
                return Response(
                    {'errors': 'Вы не можете подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FollowSerializer(
                data={'user': request.user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            author = get_object_or_404(User, id=id)
            if not Follow.objects.filter(user=request.user,
                                         author=author).exists():
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.get(user=request.user.id,
                               author=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientGetSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient', 'tags'
        ).all()
        return recipes

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['post', 'delete'], detail=True, url_path='favorite', permission_classes=[IsAuthenticated])
    def favorites(self, request, pk=None):
        if request.method == 'POST':
            recipe = self.get_object()
            user = request.user
            serializer = FavoriteSerializer(data={'user': user.id, 'recipe': recipe.id})
            if serializer.is_valid(raise_exception=True) and user != recipe.author:
                serializer.save()
                return Response({'message': 'Рецепт успешно добавлен в избранное'}, status=status.HTTP_201_CREATED)
            return Response({'message': 'Ошибка добавления в избранное'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            recipe = self.get_object()
            user = request.user.id
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            if request.user != favorite.user:
                return Response({'message': 'Ошибка отписки'},
                                status=status.HTTP_403_FORBIDDEN)
            favorite.delete()
            return Response({'message': f'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT)

        return Response({'message': 'Метод не поддерживается'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
