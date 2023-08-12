import base64

from django.core.files.base import ContentFile
from django.core.validators import MaxLengthValidator, RegexValidator
from djoser.serializers import UserSerializer
from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from .models import Follow, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            MaxLengthValidator(
                254,
                message="Длина email не должна превышать 254 символа."
            ),
        ],
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(regex=r"^[\w.@+-]+$",),
            MaxLengthValidator(150),
        ]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[
            MaxLengthValidator(
                150,
                message="Длина пароля не должна превышать 150 символов."
            ),
        ],

    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password',)
        write_only_fields = ('password',)

    def validate_username(self, value):
        if value == "me":
            raise serializers.ValidationError("Нельзя использовать имя 'me'")
        return value

    def to_representation(self, instance):
        """Исключаем из ответа поле is_subscribed при регистрации."""
        data = super().to_representation(instance)
        if self.context.get('view').action == 'create':
            data.pop('is_subscribed', None)
        return data

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserGetSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',
                  )

    def get_is_subscribed(self, obj):
        user_id = self.context.get('request').user.id
        return Follow.objects.filter(
            author=obj.id,
            user=user_id
        ).exists()


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

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        """Статус - рецепт в избранном или нет."""
        user_id = self.context.get('request').user.id
        return Favorite.objects.filter(
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
        for ingredient_data in ingredients:
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ).save()
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

        instance.recipe_ingredients.all().delete()

        for ingredient_data in ingredients_data:
            ingredient_name = ingredient_data.get('ingredient')
            ingredient = Ingredient.objects.get(name=ingredient_name)
            if ingredient:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )

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


class SubscriptionsSerializer(UserGetSerializer):
    recipes = RecipeSmallSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Подписка уже существует.'
            )
        ]
