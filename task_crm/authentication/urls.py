from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/",views.register,name='register'),
    path("login/",views.login,name='login'),
    path("profile/",views.profile,name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('token-refresh/',TokenRefreshView.as_view(),name = 'refresh-token'),
]
