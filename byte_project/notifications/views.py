"""Views for the notifications app."""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from notifications.models import Notification


@login_required
def notification_list(request):
    """Display the current user's notifications with pagination."""
    tab = request.GET.get('tab', 'all')
    
    if tab == 'mentions':
        notifications = Notification.objects.filter(
            recipient=request.user,
            message__icontains=f'@{request.user.username}'
        ).select_related('sender', 'recipe')
    else:
        notifications = Notification.objects.filter(
            recipient=request.user
        ).select_related('sender', 'recipe')

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'notifications/list.html', {
        'page_obj': page_obj,
        'notifications': page_obj,
        'tab': tab,
    })


@login_required
@require_POST
def mark_read(request, pk):
    """Mark a single notification as read. Returns JSON response."""
    notification = get_object_or_404(
        Notification, pk=pk, recipient=request.user
    )
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def mark_all_read(request):
    """Mark all of the current user's notifications as read."""
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)

    # Handle AJAX vs regular request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})

    return redirect('notifications:list')
