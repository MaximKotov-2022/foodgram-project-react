from django.contrib import admin
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredient(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredient,)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass
