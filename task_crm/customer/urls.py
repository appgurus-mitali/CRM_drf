from django.urls import path
from . import views

urlpatterns = [
    path('companies/', views.company_list_create_view, name='company-list-create'),
    path('companies/<int:pk>/', views.company_detail_view, name='company-detail'),

    path('contacts/', views.contact_list_create_view, name='contact-list-create'),
    path('contacts/<int:pk>/', views.contact_detail_view, name='contact-detail'),
    path('contacts/<int:pk>/company_id/', views.add_company_contact_view, name='contact-assign'),
]
"""
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc4NTE3MzQ4NiwiaWF0IjoxNzg1MTMwMjg2LCJqdGkiOiI4NDBlYWVkNjJkMDI0ZTE4OTkyODAyMGZjYTE5NTIyOCIsInVzZXJfaWQiOiI1IiwiZW1haWwiOiJtYW5hZ2VyMUBhYmMuaW4iLCJ1c2VybmFtZSI6Im1hbmFnZXIxIn0.QPHILY9oCRDgNw6PU5BRco-nHfxf0s856fq6_PBw5H8
"""