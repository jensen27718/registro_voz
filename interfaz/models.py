from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre único para la categoría (ej: Comida, Transporte, Oficina)"
    )

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().capitalize()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['nombre']


class Cuenta(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre único para la cuenta (ej: Banco Principal, Efectivo)"
    )

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().capitalize()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['nombre']


class Cliente(models.Model):
    nombre = models.CharField(max_length=150, unique=True, help_text="Nombre del cliente")

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']


class Registro(models.Model):
    fecha = models.DateField()
    descripcion = models.CharField(max_length=255, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.SET_NULL, null=True, blank=True)
    egresos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ingresos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.fecha} - {self.descripcion}"

    class Meta:
        ordering = ['-fecha', '-id']
