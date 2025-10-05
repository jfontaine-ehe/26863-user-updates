"""
URL configuration for clientUpdates project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.root_redirect, name='root-redirect'),
    path('login/', views.CustomLoginView.as_view(), name='login'), 
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('payment_dashboard/', views.payment_dashboard, name='payment_dashboard'),
    path('payment_details/', views.payment_details, name = 'payment_details'),
    path('landing_page/', views.landing_page, name = 'landing_page'),
    path('data_display/<str:claim>/', views.data_display, name = 'data_display'),
    path('<str:pwsid>/source/<path:source_name>/', views.source_detail_view, name='source-detail'),
    path('update-pfas-result/', views.update_pfas_result_view, name='update-pfas-result'),
    path('update-max-flow-rate/', views.update_max_flow_rate_view, name='update-max-flow-rate'),
    path('update-annual-production/', views.update_annual_production_view, name='update-annual-production'),
    path('contact/', views.contact_view, name='contact_default'),
    path('contact/<path:source_name>/<int:message>', views.contact_view, name='contact_phase1'),
    path('activity/', views.activity_view, name='activity')

]
