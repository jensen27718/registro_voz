from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.catalogo_view, name='catalogo'),
    path('api/cliente/', views.cliente_create, name='cliente_create'),
    path('api/cliente/detail/', views.cliente_detail, name='cliente_detail'),
    path('api/pedido/', views.pedido_create, name='pedido_create'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/pedido/<int:pedido_id>/estado/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),

    ]
