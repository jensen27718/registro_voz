from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('catalogo', '0003_tipoproducto_imagen'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID', default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cliente',
            name='telefono',
            field=models.CharField(max_length=20, db_index=True),
        ),
    ]
