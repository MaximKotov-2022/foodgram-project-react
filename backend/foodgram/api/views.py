from api.serializers import (RecipeCreateSerializer, RecipeSerializer,
                             TagSerializer, UserCreateSerializer,
                             UserGetSerializer)
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import Recipe, Tag
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

    @action(methods=['get'], detail=True, url_path='subscriptions', permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=request.user).all()
        paginator = PageNumberPagination()
        paginated_subscriptions = paginator.paginate_queryset(subscriptions, request)
        serializer = self.get_serializer(paginated_subscriptions, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        subscription = Follow.objects.filter(
            author=author,
            user=user,)

        if request.method == 'POST':
            queryset = Follow.objects.get_or_create(
                author=author,
                user=user)
            serializer = UserGetSerializer(
                author,
                context={'request': request}
            )
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            subscription.delete()
            serializer = UserGetSerializer(
                author,
                context={'request': request}
            )
            return Response(data=serializer.data, status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    pass


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
