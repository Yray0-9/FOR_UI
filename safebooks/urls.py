"""
URL configuration for safebooks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path
from django.views.generic import RedirectView

from safebooks import views

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path(
        'favicon.ico',
        RedirectView.as_view(url=staticfiles_storage.url('images/Logo_safebooks.png'), permanent=False),
    ),
    path('', views.home_page_view, name='home'),
    path('login/', views.login_page_view, name='login'),
    path('signup/', views.signup_page_view, name='signup'),
    path('register/', views.signup_page_view, name='register'),
    path('api/auth/login/', views.login_view, name='api_login'),
    path('api/auth/register/', views.register_view, name='api_register'),
    path('api/auth/logout/', views.logout_view, name='api_logout'),
    path('api/clients/', views.clients_api_view, name='api_clients'),
    path('api/clients/<int:client_id>/', views.client_detail_api_view, name='api_client_detail'),
    path('api/dashboard/summary/', views.dashboard_summary_api_view, name='api_dashboard_summary'),
    path('api/analytics/summary/', views.analytics_summary_api_view, name='api_analytics_summary'),
    path('api/reports/print-layout/', views.reports_print_layout_api_view, name='api_reports_print_layout'),
    path('api/financial-records/clients/', views.financial_record_clients_api_view, name='api_financial_record_clients'),
    path('api/financial-records/client/<int:client_id>/records/', views.financial_records_api_view, name='api_financial_records'),
    path('api/financial-records/client/<int:client_id>/records/<int:record_id>/', views.financial_record_detail_api_view, name='api_financial_record_detail'),
    path('admin/', views.admin_dashboard_page_view, name='admin_root'),
    path('admin/dashboard/', views.admin_dashboard_page_view, name='admin_dashboard'),
    path('admin/bookkeepers/', views.admin_bookkeepers_page_view, name='admin_bookkeepers'),
    path('admin/approvals/', views.admin_approvals_page_view, name='admin_approvals'),
    path('admin/audit-log/', views.admin_audit_log_page_view, name='admin_audit_log'),
    path('admin/system-settings/', views.admin_system_settings_page_view, name='admin_system_settings'),
    path('admin/profile/', views.admin_profile_page_view, name='admin_profile'),
    path('dashboard/', views.dashboard_page_view, name='dashboard'),
    path('clients/', views.clients_page_view, name='clients'),
    path('financial-records/', views.financial_records_page_view, name='financial_records'),
    path('financial-records/client/', views.financial_records_client_page_view, name='financial_records_client'),
    path('analytics/', views.analytics_page_view, name='analytics'),
    path('reports/', views.reports_page_view, name='reports'),
    path('settings/', views.settings_page_view, name='settings'),
    path('profile/', views.profile_page_view, name='profile'),
]
