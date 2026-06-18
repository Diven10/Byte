"""
Admin configuration for the accounts application.

Registers the Profile model with a custom inline on the User admin.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    """Inline admin for Profile model, displayed on the User admin page."""

    model = Profile
    can_delete = False
    verbose_name = 'Profile'
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    """Extended User admin that includes the Profile inline."""

    inlines = [ProfileInline]

    def get_inline_instances(self, request, obj=None):
        """Only show inline instances when editing an existing user."""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Unregister the default User admin and register with our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin configuration for the Profile model."""

    list_display = ['user', 'bio']
    search_fields = ['user__username', 'user__email', 'bio']
    raw_id_fields = ['user']
