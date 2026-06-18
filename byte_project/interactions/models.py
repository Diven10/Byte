"""Models for social interactions: likes, comments, bookmarks, and follows."""

from django.db import models
from django.db.models import CheckConstraint, F, Q
from django.contrib.auth.models import User


class Like(models.Model):
    """Represents a user liking a recipe."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='likes'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe', on_delete=models.CASCADE, related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} likes {self.recipe.title}'


class Comment(models.Model):
    """Represents a user comment on a recipe."""

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe', on_delete=models.CASCADE, related_name='comments'
    )
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.username} on {self.recipe.title}'


class Bookmark(models.Model):
    """Represents a user bookmarking a recipe for later."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bookmarks'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe', on_delete=models.CASCADE, related_name='bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} bookmarked {self.recipe.title}'


class Follow(models.Model):
    """Represents a user following another user."""

    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following_set'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']
        constraints = [
            CheckConstraint(
                check=~Q(follower=F('following')),
                name='prevent_self_follow',
            ),
        ]

    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'
