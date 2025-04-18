from django.urls import path
from .views import register, home, user_login, user_logout, dashboard, profile

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('', home, name='home'),
    # protected routes only post login
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
]
