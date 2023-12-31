import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            Tag,
                            ShoppingCart)

from users.models import User
from users.serializers import UserGetSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSmallSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с краткой информацией о рецепте."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(RecipeSmallSerializer):
    tags = TagSerializer(many=True, read_only=True,)
    is_favorited = serializers.SerializerMethodField()
    author = UserGetSerializer(read_only=True,)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredients',
                                             read_only=True,)
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'name', 'image', 'text',
                  'is_in_shopping_cart',
                  'cooking_time')

    def get_is_favorited(self, obj):
        """Статус - рецепт в избранном или нет."""
        user_id = self.context.get('request').user.id
        return Favorite.objects.filter(
            user=user_id, recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """Статус - рецепт в избранном или нет."""
        user_id = self.context.get('request').user.id
        return ShoppingCart.objects.filter(
            user=user_id, recipe=obj.id).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("author", "ingredients", "tags", "name", "image", "text",
                  "cooking_time")

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance = super().create(validated_data)
        recipe_ingredients = []
        for ingredient_data in ingredients:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient_data['ingredient'],
                    amount=ingredient_data['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return instance

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class RecipePartialUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )
    ingredients = RecipeIngredientCreateSerializer(many=True, required=False)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('name', 'text', 'image', 'cooking_time', 'tags',
                  'ingredients')

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)

        instance.save()

        RecipeIngredient.objects.filter(recipe=instance).delete()
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_name = ingredient_data.get('ingredient')
            ingredient = Ingredient.objects.get(name=ingredient_name)
            if ingredient:
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=instance,
                        ingredient=ingredient,
                        amount=ingredient_data['amount']
                    )
                )

        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        instance.tags.set(tags)
        return instance

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class IngredientGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Подписка уже существует.'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в корзине.'
            )
        ]


class SubscriptionsSerializer(UserGetSerializer):
    recipes = RecipeSmallSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)
