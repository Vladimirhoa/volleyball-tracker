from django.urls import path
from . import views

urlpatterns = [
    path('', views.match_list, name='match_list'),
    path('add/', views.match_create, name='match_create'),
    path('<int:match_id>/', views.match_detail, name='match_detail'),
    path('<int:match_id>/add_video/', views.video_create, name='video_create'),
    path('<int:match_id>/delete/', views.match_delete, name='match_delete'),
    path('video/<int:video_id>/delete/', views.video_delete, name='video_delete'),
    path('video/<int:video_id>/progress/', views.video_progress, name='video_progress'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),
    path('shared/match/<uuid:share_token>/', views.public_match_view, name='public_match'),
    path('shared/video/<uuid:share_token>/', views.public_video_view, name='public_video'),
]