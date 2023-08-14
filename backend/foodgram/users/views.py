from api.serializers import SubscriptionsSerializer
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Follow, User
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import FollowSerializer, UserGetSerializer


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)


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
