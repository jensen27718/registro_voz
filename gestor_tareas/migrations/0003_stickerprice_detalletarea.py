from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestor_tareas', '0002_alter_tarea_options_tarea_orden'),
    ]

    operations = [
        migrations.CreateModel(
            name='StickerPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_producto', models.CharField(choices=[('GLOBO', 'Stickers para globos'), ('CINTA', 'Stickers para cintas')], max_length=10)),
                ('tamano', models.CharField(max_length=50)),
                ('color', models.CharField(max_length=50)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
            options={
                'ordering': ['tipo_producto', 'tamano', 'color'],
                'unique_together': {('tipo_producto', 'tamano', 'color')},
            },
        ),
        migrations.CreateModel(
            name='DetalleTarea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_producto', models.CharField(choices=[('GLOBO', 'Stickers para globos'), ('CINTA', 'Stickers para cintas'), ('LOGO', 'Stickers de logos')], max_length=10)),
                ('referencia', models.CharField(blank=True, help_text='Código de referencia para productos existentes.', max_length=100)),
                ('descripcion', models.CharField(blank=True, help_text='Texto del sticker para referencias personalizadas.', max_length=200)),
                ('datos_adicionales', models.TextField(blank=True)),
                ('tamano', models.CharField(blank=True, max_length=50)),
                ('color', models.CharField(blank=True, max_length=50)),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('precio_unitario', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('imagen_url', models.URLField(blank=True)),
                ('completado', models.BooleanField(default=False)),
                ('tarea', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='gestor_tareas.tarea')),
            ],
        ),
    ]

