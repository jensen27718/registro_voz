# gestor_tareas/admin.py
from django.contrib import admin
from .models import TipoTrabajo, Tarea, DetalleTarea, StickerPrice

@admin.register(TipoTrabajo)
class TipoTrabajoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


class DetalleTareaInline(admin.TabularInline):
    model = DetalleTarea
    extra = 0


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo', 'estado', 'prioridad', 'fecha_recibido', 'fecha_completado')
    list_filter = ('estado', 'prioridad', 'tipo', 'fecha_recibido')
    search_fields = ('cliente', 'numero', 'id')
    list_editable = ('estado', 'prioridad')
    date_hierarchy = 'fecha_recibido'
    inlines = [DetalleTareaInline]


@admin.register(StickerPrice)
class StickerPriceAdmin(admin.ModelAdmin):
    list_display = ('tipo_producto', 'tamano', 'color', 'precio')
    list_filter = ('tipo_producto', 'tamano', 'color')
    search_fields = ('tamano', 'color')


@admin.register(DetalleTarea)
class DetalleTareaAdmin(admin.ModelAdmin):
    list_display = ('tarea', 'tipo_producto', 'referencia', 'descripcion', 'cantidad', 'completado')
    list_filter = ('tipo_producto', 'completado')
    search_fields = ('referencia', 'descripcion')
