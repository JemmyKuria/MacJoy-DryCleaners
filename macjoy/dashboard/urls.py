from django.urls import path
from . import views

urlpatterns = [
    path('attendant/', views.attendant_dashboard, name='attendant_dashboard'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('settings/', views.settings, name='settings'),
    path('settings/toggle/<int:user_id>/', views.toggle_attendant, name='toggle_attendant'),
]