from api.views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                       SubscriptionsViewSet, TagViewSet)
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet)
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('users/subscriptions/',
         SubscriptionsViewSet.as_view({'get': 'subscriptions'})),
    path('users/<int:id>/subscribe/',
         SubscriptionsViewSet.as_view(
             {'post': 'subscribe',
              'delete': 'subscribe'}
         )),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
