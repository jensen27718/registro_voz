# catalogo/admin.py

from django.contrib import admin
from .models import (
    Cliente,
    Administrador,
    TipoProducto,
    Categoria,
    Producto,
    AtributoDef,
    ValorAtributo,
    VariacionProducto,
    Promo,
    Carrito,
    CarritoItem,
    Pedido,
    PedidoItem,
)

# 1. Creamos una clase para personalizar la vista de CarritoItem
class CarritoItemInline(admin.TabularInline):
    model = CarritoItem
    extra = 0 # Para no mostrar formularios extra para añadir items
    readonly_fields = ('variacion', 'cantidad') # Hacemos los campos de solo lectura aquí

# 2. Creamos una clase para personalizar la vista de Carrito
@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'creado', 'item_count') # Campos a mostrar en la lista
    list_filter = ('creado',)
    search_fields = ('cliente__nombre', 'cliente__telefono') # Permitir buscar por nombre o teléfono del cliente
    inlines = [CarritoItemInline] # Mostrar los items del carrito directamente en la página del carrito

    @admin.display(description='Número de Items')
    def item_count(self, obj):
        return obj.items.count()

# 3. Hacemos lo mismo para Pedido
class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0
    readonly_fields = ('variacion', 'cantidad', 'precio_unitario')

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'estado', 'item_count')
    list_filter = ('estado', 'fecha')
    search_fields = ('cliente__nombre', 'cliente__telefono')
    inlines = [PedidoItemInline]

    @admin.display(description='Número de Items')
    def item_count(self, obj):
        return obj.items.count()

# 4. Personalizamos la vista de Cliente para ver sus pedidos y carritos
class PedidoInline(admin.StackedInline):
    model = Pedido
    extra = 0
    show_change_link = True # Permite hacer clic para ir al pedido
    fields = ('fecha', 'estado')
    readonly_fields = ('fecha', 'estado')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'direccion', 'ciudad')
    search_fields = ('nombre', 'telefono')
    inlines = [PedidoInline] # Mostramos los pedidos directamente en la vista del cliente


# Registramos el resto de los modelos de la forma simple
admin.site.register(Administrador)
admin.site.register(TipoProducto)
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(AtributoDef)
admin.site.register(ValorAtributo)
admin.site.register(VariacionProducto)
admin.site.register(Promo)
# Ya no necesitamos registrar Carrito, Pedido y Cliente aquí, porque usamos el decorador @admin.register
# admin.site.register(Carrito) 
# admin.site.register(Pedido)
# admin.site.register(Cliente)
admin.site.register(CarritoItem)
admin.site.register(PedidoItem)