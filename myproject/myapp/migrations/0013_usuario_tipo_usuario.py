# Generated by Django 5.1.1 on 2024-11-01 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_remove_usuario_edad_usuario_fecha_nacimiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='tipo_usuario',
            field=models.CharField(choices=[('estudiante', 'Estudiante'), ('administrador', 'Administrador')], default='estudiante', max_length=20),
        ),
    ]