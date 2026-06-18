"""URL configuration for the accounts application."""

from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.settings_view, name='settings'),
    path('accessibility/', views.accessibility_view, name='accessibility'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/followers/', views.followers_list, name='followers'),
    path('profile/<str:username>/following/', views.following_list, name='following'),
]
