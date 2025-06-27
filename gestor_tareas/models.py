# gestor_tareas/models.py

from django.db import models
from django.utils import timezone

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
    
    fecha_completado = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha en que la tarea cambió a estado 'Completado'. Se rellena automáticamente."
    )
    
    is_visible = models.BooleanField(
        default=True, 
        help_text="Indica si la tarea es visible en la lista principal. Desmarcar para archivar."
    )

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
        # Ordena las tareas por fecha de recibido (más nuevas primero) y luego por prioridad.
        ordering = ['-fecha_recibido', 'prioridad']