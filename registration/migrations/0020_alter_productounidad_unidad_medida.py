# Generated by Django 5.1.2 on 2025-06-14 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0019_alter_merma_options_remove_merma_activo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productounidad',
            name='unidad_medida',
            field=models.CharField(choices=[('kg', 'Kg'), ('unidad', 'Unidad'), ('caja', 'Caja')], max_length=10),
        ),
    ]
