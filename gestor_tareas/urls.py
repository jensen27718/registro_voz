# gestor_tareas/urls.py
from django.urls import path
from . import views

app_name = 'gestor_tareas'

urlpatterns = [
    path('', views.listar_tareas, name='lista_tareas'),
    path('agregar/', views.agregar_tarea_voz, name='agregar_tarea_voz'),
    path('analizar/', views.analizar_texto_tarea, name='analizar_tarea'),
    path('registrar/', views.registrar_tarea, name='registrar_tarea'),
    path('crear/tipo/', views.crear_tipo_trabajo, name='crear_tipo'),
    path('actualizar-estado/', views.actualizar_estado_tarea, name='actualizar_estado'),
    
    # <-- NUEVAS RUTAS -->
    path('editar/<int:tarea_id>/', views.editar_tarea, name='editar_tarea'),
    path('ocultar/<int:tarea_id>/', views.ocultar_tarea, name='ocultar_tarea'),
]