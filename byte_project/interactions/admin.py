"""Admin configuration for the interactions app."""

from django.contrib import admin

from interactions.models import Like, Comment, Bookmark, Follow


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Admin interface for Like model."""

    list_display = ['user', 'recipe', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['user', 'recipe']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model."""

    list_display = ['author', 'recipe', 'text_preview', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['author', 'recipe']
    search_fields = ['text']

    def text_preview(self, obj):
        """Return the first 50 characters of the comment text."""
        return obj.text[:50]

    text_preview.short_description = 'Text Preview'


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    """Admin interface for Bookmark model."""

    list_display = ['user', 'recipe', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['user', 'recipe']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Admin interface for Follow model."""

    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['follower', 'following']
