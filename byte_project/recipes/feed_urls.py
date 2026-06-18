"""
Feed URL configuration.

Serves the root-level feed pages: home and explore.
Mounted at the root URL '' in the project's main urls.py.
"""

from django.urls import path

from . import views

app_name = 'feed'

urlpatterns = [
    path('', views.home_feed, name='home'),
    path('explore/', views.explore_view, name='explore'),
]
