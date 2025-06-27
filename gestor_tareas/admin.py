# gestor_tareas/admin.py
from django.contrib import admin
from .models import TipoTrabajo, Tarea

@admin.register(TipoTrabajo)
class TipoTrabajoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo', 'estado', 'prioridad', 'fecha_recibido', 'fecha_completado')
    list_filter = ('estado', 'prioridad', 'tipo', 'fecha_recibido')
    search_fields = ('cliente', 'numero', 'id')
    list_editable = ('estado', 'prioridad')
    date_hierarchy = 'fecha_recibido'