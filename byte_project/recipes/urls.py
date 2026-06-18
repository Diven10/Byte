"""URL configuration for the recipes application."""

from django.urls import path

from . import views

app_name = 'recipes'

urlpatterns = [
    path('create/', views.recipe_create, name='create'),
    path('<int:pk>/', views.recipe_detail, name='detail'),
    path('<int:pk>/edit/', views.recipe_edit, name='edit'),
    path('<int:pk>/delete/', views.recipe_delete, name='delete'),
    path('search/', views.search_view, name='search'),
    path('hashtag/<slug:slug>/', views.hashtag_view, name='hashtag'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('trending/', views.trending_view, name='trending'),
]
