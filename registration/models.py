from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404, redirect


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group)
    token_app_session = models.CharField(max_length = 240,null=True, blank=True, default='')
    first_session = models.CharField(max_length = 240,null=True, blank=True, default='Si')
    rut = models.CharField(max_length=12, unique=True)  # RUT del usuario
    telefono = models.CharField(max_length=12, blank=True, null=True)  # Teléfono de contacto
    fecha_nacimiento = models.DateField(blank=True, null=True)  # Fecha de nacimiento
    direccion = models.CharField(max_length=255, blank=True, null=True)  # Dirección
    sexo = models.CharField(max_length=1, choices=(('M', 'Masculino'), ('F', 'Femenino')), blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ['user__username']
    def __str__(self):
        return f'{self.user.username} ({self.rut})'
