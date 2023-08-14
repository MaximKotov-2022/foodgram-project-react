from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.serializers import (FavoriteSerializer, FollowSerializer,
                             IngredientGetSerializer, RecipeCreateSerializer,
                             RecipePartialUpdateSerializer, RecipeSerializer,
                             RecipeSmallSerializer, SubscriptionsSerializer,
                             TagSerializer, UserGetSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

from .filters import IngredientFilter, RecipeFilter
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

    @action(methods=['get'], detail=True, url_path='subscriptions',
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=request.user).all()
        paginator = PageNumberPagination()
        paginated_subscriptions = paginator.paginate_queryset(subscriptions,
                                                              request)
        serializer = self.get_serializer(paginated_subscriptions, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe',
            permission_classes=[IsAuthenticated])
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
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient', 'tags'
        ).all()

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        elif self.action == 'partial_update':
            return RecipePartialUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['get', 'post', 'delete'], detail=True,
            url_path='favorite', permission_classes=[IsAuthenticated])
    def favorites(self, request, pk=None):
        if request.method == 'POST':
            recipe = self.get_object()
            user = request.user
            serializer = FavoriteSerializer(
                data={
                    'user': user.id,
                    'recipe': recipe.id}
            )
            if (serializer.is_valid(raise_exception=True)
                    and user != recipe.author):
                serializer.save()
                return Response({
                    'message': 'Рецепт успешно добавлен в избранное'},
                    status=status.HTTP_201_CREATED)
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
            return Response({'message': 'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Метод не поддерживается'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.tags.set(serializer.validated_data.get('tags',
                                                        instance.tags.all()))
        return Response(serializer.data)

    def add(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if relation.exists():
            return Response(
                {'errors': f'Нельзя повторно добавить рецепт в {name}'},
                status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeSmallSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_relation(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response(
                {'errors': f'Нельзя повторно удалить рецепт из {name}'},
                status=status.HTTP_400_BAD_REQUEST)
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        if request.method == 'POST':
            name = 'список покупок'
            return self.add(ShoppingCart, user, pk, name)
        name = 'списка покупок'
        return self.delete_relation(ShoppingCart, user, pk, name)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=ShoppingCart.objects.filter(
                user=request.user
            ).values('recipe')
        )
        filename = 'shopping_cart.txt'
        response = HttpResponse(content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        content = [
            f"{ingredient.ingredient.name} - {ingredient.amount} "
            f"{ingredient.ingredient.measurement_unit}\n"
            for ingredient in ingredients
        ]
        content = ''.join(content).encode('utf-8')
        response.content = content
        return response
