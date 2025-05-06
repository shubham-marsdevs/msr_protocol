from django.urls import path
from msr_control import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]
