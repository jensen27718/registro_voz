from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('catalogo', '0004_cliente_id_autofield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='telefono',
            field=models.CharField(max_length=20, unique=True, db_index=True),
        ),
    ]
