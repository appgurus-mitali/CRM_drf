from django.urls import path
from . import views

urlpatterns = [
    # path('',views.lead_view,name='leadapi'),
    path('create/',views.create_leadview,name='create'),
    path('leads/',views.lead_view,name='lead_list'),
    path('leads/<int:pk>/',views.lead_view,name='lead_crud'),
    path('leads/<int:pk>/assign/', views.lead_assign_view, name='lead_assign'),
    path('leads/<int:pk>/status/', views.lead_status_update_view, name='lead_status_update'),
]
