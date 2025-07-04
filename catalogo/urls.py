# catalogo/urls.py

from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.catalogo_view, name='catalogo'),
    path('api/cliente/', views.cliente_create, name='cliente_create'),
    path('api/cliente/detail/', views.cliente_detail, name='cliente_detail'),
    path('api/cart/', views.cart_view, name='cart_view'),
    path('api/pedido/', views.pedido_create, name='pedido_create'),
    path('api/productos/', views.api_productos, name='api_productos'),
    path('api/productos/<int:producto_id>/', views.api_producto_detail, name='api_producto_detail'),

    # Rutas del Admin Dashboard
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/pedido/<int:pedido_id>/estado/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),
    # --- NUEVA RUTA PARA EL PDF ---
    path('admin/pedido/<int:pedido_id>/pdf/', views.generar_pedido_pdf, name='generar_pedido_pdf'),
    path('admin/valores-producto/', views.valores_por_producto, name='valores_por_producto'),
]