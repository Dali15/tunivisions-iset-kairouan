from django.urls import path
from . import views

urlpatterns = [
    path('', views.member_list, name='member_list'),
    path('<int:user_id>/edit/', views.manage_member_profile, name='manage_member_profile'),
    path('<int:user_id>/', views.member_profile, name='member_profile'),
    path('me/edit/', views.edit_profile, name='edit_profile'),
]
