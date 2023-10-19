from django.urls import path
from . import views
from .views import create_community_view

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('cart/', views.cart, name='cart'),
    path('notifications/', views.notifications, name='notifications'),
    path('messages/', views.messages, name='messages'),
    path('explore/', views.explore, name='explore'),
    path('r/<str:community_name>/', views.view_community, name='view_community'),
    path('create/', create_community_view, name='create_community'),
    path('create_post/<int:community_id>/', views.create_post_view, name='create_post'),
    

    # Agrega más paths conforme necesites
]
