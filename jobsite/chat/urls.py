from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<str:room_name>/', views.room_detail, name='room_detail'),
]
