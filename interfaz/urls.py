# interfaz/urls.py
from django.urls import path
from . import views

app_name = 'interfaz' # <-- AÑADIR ESTA LÍNEA

urlpatterns = [
    path('', views.home, name='home'),
    path('analizar/', views.analizar_texto, name='analizar'),
    path('registrar/', views.registrar_datos, name='registrar'),
    # --- NUEVAS RUTAS PARA CREACIÓN DINÁMICA ---
    path('crear/categoria/', views.crear_categoria, name='crear_categoria'),
    path('crear/cuenta/', views.crear_cuenta, name='crear_cuenta'),
]