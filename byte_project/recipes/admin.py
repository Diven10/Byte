"""
Admin configuration for the recipes application.

Registers Category, Hashtag, Recipe, and Rating models with
customized admin interfaces.
"""

from django.contrib import admin

from .models import Category, Hashtag, Rating, Recipe


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for the Category model."""

    list_display = ['name', 'slug', 'icon']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    """Admin configuration for the Hashtag model."""

    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin configuration for the Recipe model."""

    list_display = ['title', 'author', 'category', 'cooking_time', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'short_description', 'ingredients']
    raw_id_fields = ['author']
    filter_horizontal = ['hashtags']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin configuration for the Rating model."""

    list_display = ['user', 'recipe', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['user__username', 'recipe__title']
    raw_id_fields = ['user', 'recipe']
