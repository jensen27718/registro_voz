# gestor_tareas/models.py

from decimal import Decimal

from django.db import models
from django.utils import timezone

from catalogo.models import (
    TipoProducto as CatalogoTipoProducto,
    VariacionProducto,
    VariacionBase,
    ValorAtributo,
)

class TipoTrabajo(models.Model):
    """
    Define las categorías de trabajo que se pueden realizar,
    como "Globos", "Stickers", "Impresos", etc.
    """
    nombre = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nombre único para el tipo de trabajo (ej: Globos, Stickers)."
    )

    def save(self, *args, **kwargs):
        # Asegura que el nombre siempre se guarde capitalizado y sin espacios extra.
        self.nombre = self.nombre.strip().capitalize()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        # Ordena los tipos de trabajo alfabéticamente por defecto.
        ordering = ['nombre']

class Tarea(models.Model):
    """
    Representa una tarea o pedido individual en el sistema.
    """

    # --- Opciones predefinidas para campos de elección (Choices) ---
    class Prioridad(models.TextChoices):
        URGENTE = 'Urgente', 'Urgente'
        NORMAL = 'Normal', 'Normal'

    class Estado(models.TextChoices):
        RECIBIDO = 'Recibido', 'Recibido'
        EN_PROCESO = 'En Proceso', 'En Proceso'
        COMPLETADO = 'Completado', 'Completado'

    # --- Definición de los campos de la tabla Tarea ---

    fecha_recibido = models.DateField(
        default=timezone.now,
        help_text="Fecha en que se recibió la tarea."
    )
    
    prioridad = models.CharField(
        max_length=10, 
        choices=Prioridad.choices, 
        default=Prioridad.NORMAL,
        help_text="Nivel de urgencia de la tarea."
    )
    
    estado = models.CharField(
        max_length=20, 
        choices=Estado.choices, 
        default=Estado.RECIBIDO,
        help_text="Estado actual de la tarea."
    )
    
    cliente = models.CharField(
        max_length=150,
        help_text="Nombre del cliente que solicita la tarea."
    )
    
    tipo = models.ForeignKey(
        TipoTrabajo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Categoría o tipo de trabajo a realizar."
    )
    
    telefono = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        help_text="Número de teléfono opcional del cliente."
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada de la tarea."
    )

    orden = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número que define el orden de prioridad de la tarea."
    )
    
    fecha_completado = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha en que la tarea cambió a estado 'Completado'. Se rellena automáticamente."
    )
    
    is_visible = models.BooleanField(
        default=True,
        help_text="Indica si la tarea es visible en la lista principal. Desmarcar para archivar."
    )

    @property
    def dias_desde_recibido(self) -> int:
        """Cantidad de días transcurridos desde ``fecha_recibido``."""
        return (timezone.now().date() - self.fecha_recibido).days

    @property
    def costo_total(self):
        """Suma del costo de todos los detalles asociados."""
        total = Decimal('0')
        for det in self.detalles.all():
            total += det.precio_total
        return total

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método de guardado para añadir lógica personalizada.
        """
        # Lógica para gestionar la fecha de completado automáticamente.
        if self.estado == self.Estado.COMPLETADO and not self.fecha_completado:
            # Si se marca como completada y no tiene fecha, se asigna la de hoy.
            self.fecha_completado = timezone.now().date()
        elif self.estado != self.Estado.COMPLETADO:
            # Si se cambia de 'Completado' a otro estado, se limpia la fecha.
            self.fecha_completado = None
            
        super().save(*args, **kwargs)

    def __str__(self):
        # Representación en texto de una instancia de Tarea, útil en el admin.
        return f"Tarea #{self.id} para {self.cliente} ({self.tipo})"

    class Meta:
        # Ordena las tareas por el campo 'orden' y luego por fecha de recibido y prioridad.
        ordering = ['orden', '-fecha_recibido', 'prioridad']



class DetalleTarea(models.Model):
    """Detalle de productos dentro de una tarea."""


    tarea = models.ForeignKey(
        'Tarea',
        related_name='detalles',
        on_delete=models.CASCADE,
    )

    tipo_producto = models.ForeignKey(
        CatalogoTipoProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Tipo de producto según el catálogo.",
    )
    variacion = models.ForeignKey(
        VariacionProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Variación del catálogo para referencias existentes.",
    )

    referencia = models.CharField(
        max_length=100,
        blank=True,
        help_text="Código de referencia para productos existentes.",
    )
    descripcion = models.CharField(
        max_length=200,
        blank=True,
        help_text="Texto del sticker para referencias personalizadas.",
    )
    datos_adicionales = models.TextField(blank=True)

    tamano = models.ForeignKey(
        ValorAtributo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text="Tamaño del producto (ValorAtributo).",
    )
    color = models.ForeignKey(
        ValorAtributo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text="Color del producto (ValorAtributo).",
    )

    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    imagen_url = models.URLField(blank=True)
    completado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if self.variacion and not self.referencia:
            self.referencia = self.variacion.producto.referencia
        if self.precio_unitario is None:
            if self.variacion:
                self.precio_unitario = self.variacion.precio_base
                if not self.tipo_producto:
                    cat = self.variacion.producto.categorias.first()
                    if cat:
                        self.tipo_producto = cat.tipo_producto
                if not self.tamano or not self.color:
                    for val in self.variacion.valores.all():
                        nombre = val.atributo_def.nombre.lower()
                        if 'tam' in nombre and not self.tamano:
                            self.tamano = val
                        if 'color' in nombre and not self.color:
                            self.color = val
            elif self.tipo_producto:
                qs = VariacionBase.objects.filter(tipo_producto=self.tipo_producto)
                if self.tamano:
                    qs = qs.filter(valores=self.tamano)
                if self.color:
                    qs = qs.filter(valores=self.color)
                vb = qs.first()
                if vb:
                    self.precio_unitario = vb.precio_base

        super().save(*args, **kwargs)

    @property
    def precio_total(self):
        if self.precio_unitario is None:
            return Decimal('0')
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return self.referencia or self.descripcion or f"Detalle {self.id}"
