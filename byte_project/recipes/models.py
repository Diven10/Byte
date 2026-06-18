"""
Models for the recipes application.

Defines Category, Hashtag, Recipe, and Rating models for the
Byte recipe social media platform.
"""

import re

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """
    Recipe category model.

    Groups recipes into broad categories like 'Breakfast', 'Dessert', etc.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(
        max_length=10,
        blank=True,
        default='🍽️',
        help_text='Emoji icon for the category',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Hashtag(models.Model):
    """
    Hashtag model for recipe tagging.

    Stores hashtag names WITHOUT the '#' prefix.
    Provides a class method to parse hashtags from text.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Hashtag'
        verbose_name_plural = 'Hashtags'

    def __str__(self):
        return f'#{self.name}'

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def parse_hashtags(cls, text):
        """
        Extract hashtag strings from text and return/create Hashtag objects.

        Uses regex r'#(\\w+)' to find hashtags in the given text.
        Creates new Hashtag objects for any that don't already exist.

        Args:
            text: String potentially containing hashtags like '#vegan #healthy'.

        Returns:
            list: List of Hashtag model instances.
        """
        if not text:
            return []

        hashtag_names = re.findall(r'#(\w+)', text)
        hashtags = []

        for name in hashtag_names:
            name_lower = name.lower()
            hashtag, created = cls.objects.get_or_create(
                name=name_lower,
                defaults={'slug': slugify(name_lower)},
            )
            hashtags.append(hashtag)

        return hashtags


class Recipe(models.Model):
    """
    Recipe model — the core content of the Byte platform.

    Stores all recipe information including ingredients, instructions,
    cooking time, and relationships to categories and hashtags.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    title = models.CharField(max_length=200)
    cover_image = models.ImageField(
        upload_to='recipe_images/',
        blank=True,
        null=True,
    )
    short_description = models.TextField(max_length=500)
    ingredients = models.TextField(help_text='One ingredient per line')
    instructions = models.TextField(help_text='Step-by-step instructions')
    cooking_time = models.PositiveIntegerField(help_text='Time in minutes')
    servings = models.PositiveIntegerField(default=1)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipes',
    )
    hashtags = models.ManyToManyField(
        Hashtag,
        blank=True,
        related_name='recipes',
    )
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Return the URL for the recipe detail page."""
        return reverse('recipes:detail', args=[self.pk])

    @property
    def likes_count(self):
        """Return the total number of likes on this recipe."""
        return self.likes.count()

    @property
    def comments_count(self):
        """Return the total number of comments on this recipe."""
        return self.comments.count()

    @property
    def bookmarks_count(self):
        """Return the total number of bookmarks on this recipe."""
        return self.bookmarks.count()

    @property
    def average_rating(self):
        """Return the average rating score, or 0 if no ratings exist."""
        avg = self.ratings.aggregate(Avg('score'))['score__avg']
        return avg or 0

    @property
    def ingredients_list(self):
        """
        Return ingredients as a list, split by newline.

        Strips whitespace from each item and filters out empty lines.
        """
        return [
            line.strip()
            for line in self.ingredients.split('\n')
            if line.strip()
        ]

    @property
    def instructions_list(self):
        """
        Return instructions as a list, split by newline.

        Strips whitespace from each step and filters out empty lines.
        """
        return [
            line.strip()
            for line in self.instructions.split('\n')
            if line.strip()
        ]

    @property
    def get_cooking_time_display(self):
        """
        Return cooking time in a human-readable format.

        Examples: '45m', '1h 30m', '2h'.
        """
        if self.cooking_time < 60:
            return f'{self.cooking_time}m'
        hours = self.cooking_time // 60
        minutes = self.cooking_time % 60
        if minutes == 0:
            return f'{hours}h'
        return f'{hours}h {minutes}m'


class Rating(models.Model):
    """
    Rating model for recipe ratings.

    Each user can rate a recipe once with a score from 1 to 5.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ['-created_at']
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'

    def __str__(self):
        return f'{self.user.username} rated {self.recipe.title}: {self.score}/5'
