from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=settings.MAX_LENGTH_RECIPES_DATA)
    color = models.CharField(max_length=settings.MAX_LENGTH_RECIPES_COLOR)
    slug = models.SlugField(max_length=settings.MAX_LENGTH_RECIPES_DATA,
                            unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(
        null=True,
        default=None,
        blank=True,
    )
    name = models.CharField(max_length=settings.MAX_LENGTH_RECIPES_DATA)
    cooking_time = models.PositiveIntegerField(validators=[
        MinValueValidator(1,
                          'Время должно быть больше 1 минуты')
    ])
    text = models.TextField()
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'))

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=settings.MAX_LENGTH_RECIPES_DATA)
    measurement_unit = models.CharField(
        max_length=settings.MAX_LENGTH_RECIPES_DATA)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,
                               related_name='recipe_ingredients',
                               on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient,
                                   related_name='ingredients_recipe',
                                   on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[
        MinValueValidator(1,
                          'Количество должно быть больше 1')
    ])


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def clean(self):
        if self.user == self.recipe.author:
            raise ValidationError(
                'Вы не можете добавить свой собственный рецепт в'
                'избранное.')

    def __str__(self):
        return (f'Пользователь {self.user} добавил в избранное'
                f'рецепт {self.recipe}')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sh_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='sh_cart'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_cart_recipe'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
