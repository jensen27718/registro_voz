from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('interfaz', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150, unique=True, help_text='Nombre del cliente')),
            ],
            options={'ordering': ['nombre'],},
        ),
        migrations.CreateModel(
            name='Registro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('descripcion', models.CharField(blank=True, max_length=255)),
                ('egresos', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('ingresos', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('categoria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='interfaz.categoria')),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='interfaz.cliente')),
                ('cuenta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='interfaz.cuenta')),
            ],
            options={'ordering': ['-fecha', '-id'],},
        ),
    ]
