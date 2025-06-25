# interfaz/admin.py
from django.contrib import admin
from .models import Categoria, Cuenta

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)