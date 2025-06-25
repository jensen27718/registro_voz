# interfaz/models.py
from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="Nombre único. Se guardará con mayúscula inicial (ej: Comida)."
    )

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Forzar la capitalización antes de guardar para mantener consistencia.
        self.nombre = self.nombre.strip().capitalize()
        super(Categoria, self).save(*args, **kwargs)

    class Meta:
        ordering = ['nombre']

class Cuenta(models.Model):
    nombre = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="Nombre único. Se guardará con mayúscula inicial (ej: Banco Principal)."
    )

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Forzar la capitalización en cada guardado.
        self.nombre = self.nombre.strip().capitalize()
        super(Cuenta, self).save(*args, **kwargs)

    class Meta:
        ordering = ['nombre']