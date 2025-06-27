from django.urls import path
from . import views

app_name = 'interfaz'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analizar/', views.analizar_texto, name='analizar'),
    path('registrar/', views.registrar_datos, name='registrar'),
    path('crear/categoria/', views.crear_categoria, name='crear_categoria'),
    path('crear/cuenta/', views.crear_cuenta, name='crear_cuenta'),
    path('editar/<int:registro_id>/', views.editar_registro, name='editar_registro'),
    path('eliminar/<int:registro_id>/', views.eliminar_registro, name='eliminar_registro'),
]
