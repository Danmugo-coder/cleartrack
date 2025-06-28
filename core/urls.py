from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('scan-clearance/', views.scan_clearance, name='scan_clearance'),
    path('view-clearance/<uuid:token>/', views.view_clearance, name='view_clearance'),
    
    # ✅ Health check endpoint for Render
    path('healthz/', views.health_check, name='healthz'),
]
