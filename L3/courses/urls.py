from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('add/', views.course_create, name='course_create'),
    path('edit/<int:pk>/', views.course_update, name='course_update'),
    path('delete/<int:pk>/', views.course_delete, name='course_delete'),
]
