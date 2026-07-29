from django.urls import path
from . import views

urlpatterns = [
    path('deals/', views.deal_view, name='deal-list-create'),
    path('deals/<int:pk>/', views.deal_view, name='deal-detail-update-delete'),

    path('followups/', views.followup_view, name='followup-list-create'),
    path('followups/<int:pk>/', views.followup_view, name='followup-detail-update-delete'),

    path('notes/', views.note_view, name='note-list-create'),
    path('notes/<int:pk>/', views.note_view, name='note-detail'),

    path('dashboard/', views.dashboard_summary_view, name='dashboard'),
    path('deals/pipeline/', views.deal_pipeline_view, name='deal-pipeline-metrics'),

]