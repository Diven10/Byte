"""
URL configuration for Byte project.

Routes are organized by app:
- /              → recipes (home feed)
- /accounts/     → accounts (auth, profiles)
- /recipes/      → recipes (CRUD, detail, search)
- /interactions/  → interactions (AJAX: like, comment, bookmark, follow)
- /notifications/ → notifications (list, mark read)
- /admin/        → Django admin
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('recipes/', include('recipes.urls', namespace='recipes')),
    path('interactions/', include('interactions.urls', namespace='interactions')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    # Home feed at root
    path('', include('recipes.feed_urls', namespace='feed')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
