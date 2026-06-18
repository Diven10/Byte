"""
Global context processors for the Byte project.

These inject data into every template rendering context.
"""


def notifications_count(request):
    """Inject unread notification count into every template."""
    if request.user.is_authenticated:
        from notifications.models import Notification
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}


def global_context(request):
    """Inject global site context into every template."""
    from recipes.models import Category
    context = {
        'site_name': 'Byte',
        'all_categories': Category.objects.all().order_by('name'),
    }
    return context
