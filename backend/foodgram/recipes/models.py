from api.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from foodgram.settings import (MAX_LENGTH_EMAIL, MAX_LENGTH_PERSONAL_DATA,
                               MAX_LENGTH_RECIPES_COLOR,
                               MAX_LENGTH_RECIPES_DATA)


class Tag(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_RECIPES_DATA)
    color = models.CharField(max_length=MAX_LENGTH_RECIPES_COLOR)
    slug = models.SlugField(max_length=MAX_LENGTH_RECIPES_DATA, unique=True)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        default=None,
        blank=True,
    )
    name = models.CharField(max_length=MAX_LENGTH_RECIPES_DATA)
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

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_RECIPES_DATA)
    measurement_unit = models.CharField(max_length=MAX_LENGTH_RECIPES_DATA)

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
