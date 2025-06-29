from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.catalogo_view, name='catalogo'),
    path('api/cliente/', views.cliente_create, name='cliente_create'),
    path('api/cliente/detail/', views.cliente_detail, name='cliente_detail'),
    ]

