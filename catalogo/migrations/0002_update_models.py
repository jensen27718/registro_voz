from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('catalogo', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cliente',
            name='cedula',
        ),
        migrations.AddField(
            model_name='categoria',
            name='imagen_url',
            field=models.URLField(blank=True),
        ),
    ]
