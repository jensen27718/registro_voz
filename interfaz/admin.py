from django.contrib import admin
from .models import Categoria, Cuenta, Cliente, Registro

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'descripcion', 'cliente', 'categoria', 'cuenta', 'ingresos', 'egresos')
    list_filter = ('cliente', 'categoria', 'cuenta')
    search_fields = ('descripcion',)

