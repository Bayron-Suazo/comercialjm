# Generated by Django 5.1.2 on 2025-06-16 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0027_cliente_direccion'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='descuento_aplicado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
