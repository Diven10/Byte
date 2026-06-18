from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('explore/', views.explore, name='explore'),
    path('messages/', views.messages, name='messages'),
    path('profile/', views.profile, name='profile'),
]
