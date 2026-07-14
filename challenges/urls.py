from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_challenge, name='create_challenge'),
    path('result/<int:pk>/', views.challenge_result, name='challenge_result'),
    path('history/', views.challenge_history, name='challenge_history'),
    path('history/<int:pk>/', views.challenge_detail, name='challenge_detail'),
]
