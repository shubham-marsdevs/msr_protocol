from django.urls import path
from msr_control import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),

    # Dashboard and role-specific views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('operator/', views.operator_view, name='operator'),
    path('calibrator/', views.calibrator_view, name='calibrator'),
    path('admin/', views.admin_view, name='admin_panel'),
]
