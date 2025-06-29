from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    """Información del cliente que realiza pedidos."""
    telefono = models.CharField(primary_key=True, max_length=20)
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    cedula = models.CharField(max_length=50, blank=True)

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

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    tipo_producto = models.ForeignKey(TipoProducto, on_delete=models.CASCADE, related_name="categorias")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    class Meta:
        unique_together = ("tipo_producto", "nombre")
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="productos")
    referencia = models.CharField(max_length=100)
    nombre = models.CharField(max_length=150)
    foto_url = models.URLField(blank=True)

    class Meta:
        unique_together = ("categoria", "referencia")
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def ver_variaciones(self):
        return list(self.variaciones.all())


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


class VariacionProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="variaciones")
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    valores = models.ManyToManyField(ValorAtributo, related_name="variaciones")

    def obtener_atributo(self, nombre):
        try:
            val = self.valores.select_related("atributo_def").get(atributo_def__nombre=nombre)
            return val.valor
        except ValorAtributo.DoesNotExist:
            return ""

    def precio_con_promo(self, promo: Promo):
        if promo and promo.es_valido():
            return self.precio_base * (1 - promo.porcentaje / 100)
        return self.precio_base

    def __str__(self):
        return f"Variación {self.id} de {self.producto}"


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

    def __str__(self):
        return f"{self.cantidad} x {self.variacion}" 
