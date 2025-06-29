from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('catalogo', '0002_update_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipoproducto',
            name='imagen_url',
            field=models.URLField(blank=True),
        ),
    ]
