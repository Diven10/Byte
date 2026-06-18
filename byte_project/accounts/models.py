"""
Models for the accounts application.

Defines the Profile model that extends Django's built-in User model
with additional fields like bio and profile picture.
"""

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


class Profile(models.Model):
    """
    Extended user profile model.

    Stores additional user information beyond what Django's
    built-in User model provides, such as bio and profile picture.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.TextField(max_length=500, blank=True, default='')
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def followers_count(self):
        """Return the number of users following this user."""
        return self.user.followers.count()

    @property
    def following_count(self):
        """Return the number of users this user is following."""
        return self.user.following_set.count()

    @property
    def recipes_count(self):
        """Return the number of recipes created by this user."""
        return self.user.recipes.count()

    @property
    def get_profile_picture_url(self):
        """
        Return the profile picture URL.

        Falls back to a generated avatar from ui-avatars.com
        if no profile picture has been uploaded.
        """
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return (
            f"https://ui-avatars.com/api/"
            f"?name={self.user.username}"
            f"&background=random&color=fff&size=200"
        )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a Profile whenever a new User is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Auto-save the Profile whenever the User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
