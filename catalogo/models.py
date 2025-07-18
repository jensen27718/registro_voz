# catalogo/models.py

from django.db import models
from django.utils import timezone
from django.db.models import Sum, F # <-- Importaciones para el cálculo del total


class Cliente(models.Model):
    """Información del cliente que realiza pedidos."""
    telefono = models.CharField(max_length=20, unique=True, db_index=True)
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.telefono})"


class Administrador(models.Model):
    """Usuario administrador simple para el catálogo."""
    usuario = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=128)

    def __str__(self):
        return self.usuario


class TipoProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    imagen_url = models.URLField(blank=True)

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    tipo_producto = models.ForeignKey(TipoProducto, on_delete=models.CASCADE, related_name="categorias")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    imagen_url = models.URLField(blank=True)

    class Meta:
        unique_together = ("tipo_producto", "nombre")
        ordering = ["nombre"]

    def __str__(self):
        # Mostrar el tipo de producto para que sea más claro en formularios
        return f"{self.tipo_producto.nombre} - {self.nombre}"


# catalogo/models.py

class Producto(models.Model):
    # ELIMINAMOS EL CAMPO ANTIGUO
    # categoria = models.ForeignKey(...)

    # DEJAMOS SOLO EL CAMPO NUEVO (y podemos quitarle el blank=True si queremos que sea obligatorio)
    categorias = models.ManyToManyField(Categoria, related_name="productos")
    
    referencia = models.CharField(max_length=100)
    nombre = models.CharField(max_length=150)
    foto_url = models.URLField(blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.referencia

class AtributoDef(models.Model):
    tipo_producto = models.ForeignKey(TipoProducto, on_delete=models.CASCADE, related_name="atributos")
    nombre = models.CharField(max_length=100)

    class Meta:
        unique_together = ("tipo_producto", "nombre")
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ValorAtributo(models.Model):
    atributo_def = models.ForeignKey(AtributoDef, on_delete=models.CASCADE, related_name="valores")
    valor = models.CharField(max_length=100)
    display = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("atributo_def", "valor")
        ordering = ["valor"]

    def __str__(self):
        return self.valor


class Promo(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activo = models.BooleanField(default=True)

    def es_valido(self):
        ahora = timezone.now()
        return self.activo and self.fecha_inicio <= ahora <= self.fecha_fin

    def __str__(self):
        return self.codigo


class VariacionBase(models.Model):
    tipo_producto = models.ForeignKey(
        TipoProducto,
        on_delete=models.CASCADE,
        related_name="variaciones_base",
    )
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    valores = models.ManyToManyField(
        ValorAtributo,
        related_name="variaciones_base",
    )

    class Meta:
        ordering = ["tipo_producto__nombre"]

    def __str__(self):
        valores_str = ", ".join(v.valor for v in self.valores.all())
        return f"{self.tipo_producto.nombre} ({valores_str})"


class VariacionProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="variaciones")
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    valores = models.ManyToManyField(ValorAtributo, related_name="variaciones")

    def __str__(self):
        """Descripción de la variación usando referencia y categoría."""
        valores_str = ", ".join([v.valor for v in self.valores.all()])
        # --- LÍNEA MODIFICADA ---
        # Ya no usamos self.producto.categoria.nombre. Usamos solo la referencia.
        # Si quisieras mostrar la primera categoría, podrías hacer:
        # primera_cat = self.producto.categorias.first()
        # cat_nombre = primera_cat.nombre if primera_cat else "Sin categoría"
        return f"{self.producto.referencia} ({valores_str})"


class Carrito(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="carritos")
    promos = models.ManyToManyField(Promo, blank=True, related_name="carritos")
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito {self.id} de {self.cliente}"


class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    variacion = models.ForeignKey(VariacionProducto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("carrito", "variacion")

    def __str__(self):
        return f"{self.cantidad} x {self.variacion}"


class EstadoPedido(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    PAGADO = "PAGADO", "Pagado"
    EN_PROCESO = "EN_PROCESO", "En proceso"
    ENVIADO = "ENVIADO", "Enviado"
    ENTREGADO = "ENTREGADO", "Entregado"
    CANCELADO = "CANCELADO", "Cancelado"


class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="pedidos")
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=EstadoPedido.choices, default=EstadoPedido.PENDIENTE)
    promos = models.ManyToManyField(Promo, blank=True, related_name="pedidos")

    def __str__(self):
        return f"Pedido {self.id} para {self.cliente}"

    @property
    def total(self):
        """Calcula el total del pedido sumando los subtotales de cada item."""
        total_pedido = self.items.aggregate(
            total=Sum(F('cantidad') * F('precio_unitario'))
        )['total']
        
        # Aplicar descuento de la primera promoción válida, si existe
        if total_pedido and self.promos.exists():
            promo = self.promos.first() # Suponemos una promo por pedido
            if promo.es_valido():
                descuento = total_pedido * (promo.porcentaje / 100)
                total_pedido -= descuento

        return total_pedido or 0

    @classmethod
    def crear_desde_carrito(cls, carrito: Carrito):
        pedido = cls.objects.create(cliente=carrito.cliente)
        pedido.promos.set(carrito.promos.all())
        for item in carrito.items.all():
            PedidoItem.objects.create(
                pedido=pedido,
                variacion=item.variacion,
                cantidad=item.cantidad,
                precio_unitario=item.variacion.precio_base,
            )
        return pedido


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    variacion = models.ForeignKey(VariacionProducto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.variacion}"