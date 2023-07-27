# from django.contrib.auth import get_user_model
from api.models import User
from django.db import models

# User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    slug = models.SlugField(max_length=200, unique=True)


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag)
    name = models.CharField(max_length=200)
    cooking_time = models.PositiveIntegerField()  # Добавить валидацию на минимальное значение
    text = models.TextField()
    author = models.ForeignKey(User, related_name='recipes', on_delete=models.CASCADE)
    ingredients = models.ManyToManyField('Ingredient',
                                         through='RecipeIngredient',
                                         through_fields=('recipe', 'ingredient'))


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='recipe_ingredients', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, related_name='ingredients_recipe', on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()  # Добавить валидацию на минимальное значение
