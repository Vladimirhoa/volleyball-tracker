from django.urls import path
from . import views

urlpatterns = [
    path('', views.match_list, name='match_list'),
    path('add/', views.match_create, name='match_create'),
    path('<int:match_id>/', views.match_detail, name='match_detail'),
    path('<int:match_id>/add_video/', views.video_create, name='video_create'),
]