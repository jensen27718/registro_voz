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


admin.site.register(Cliente)
admin.site.register(Administrador)
admin.site.register(TipoProducto)
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(AtributoDef)
admin.site.register(ValorAtributo)
admin.site.register(VariacionProducto)
admin.site.register(Promo)
admin.site.register(Carrito)
admin.site.register(CarritoItem)
admin.site.register(Pedido)
admin.site.register(PedidoItem)
