from django.urls import path
from . import views

app_name = 'business_development'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('partners/', views.partner_list, name='partner_list'),
    path('partners/add/', views.partner_create, name='partner_create'),
    path('partners/<int:pk>/', views.partner_detail, name='partner_detail'),
    path('partners/<int:pk>/edit/', views.partner_edit, name='partner_edit'),
    path('partners/<int:pk>/delete/', views.partner_delete, name='partner_delete'),
    path('prospects/', views.prospect_list, name='prospect_list'),
    path('prospects/add/', views.prospect_create, name='prospect_create'),
    path('prospects/<int:pk>/', views.prospect_detail, name='prospect_detail'),
    path('prospects/<int:pk>/edit/', views.prospect_edit, name='prospect_edit'),
    path('prospects/<int:pk>/delete/', views.prospect_delete, name='prospect_delete'),
    path('opportunities/', views.opportunity_list, name='opportunity_list'),
    path('opportunities/add/', views.opportunity_create, name='opportunity_create'),
    path('opportunities/<int:pk>/', views.opportunity_detail, name='opportunity_detail'),
    path('opportunities/<int:pk>/edit/', views.opportunity_edit, name='opportunity_edit'),
    path('opportunities/<int:pk>/delete/', views.opportunity_delete, name='opportunity_delete'),
    path('interactions/', views.interaction_list, name='interaction_list'),
    path('interactions/add/', views.interaction_create, name='interaction_create'),
    path('interactions/<int:pk>/', views.interaction_detail, name='interaction_detail'),
    path('interactions/<int:pk>/edit/', views.interaction_edit, name='interaction_edit'),
    path('interactions/<int:pk>/delete/', views.interaction_delete, name='interaction_delete'),
]
