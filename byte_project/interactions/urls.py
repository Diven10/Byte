"""URL configuration for the interactions app."""

from django.urls import path

from . import views

app_name = 'interactions'

urlpatterns = [
    path('like/<int:recipe_id>/', views.toggle_like, name='toggle_like'),
    path('comment/<int:recipe_id>/', views.add_comment, name='add_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('bookmark/<int:recipe_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('saved/', views.saved_recipes, name='saved_recipes'),
    path('rate/<int:recipe_id>/', views.rate_recipe, name='rate_recipe'),
]
