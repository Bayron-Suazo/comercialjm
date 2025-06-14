from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404, redirect
from datetime import datetime, timezone


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
    failed_attempts = models.IntegerField(default=0)
    class Meta:
        ordering = ['user__username']
    def __str__(self):
        return f'{self.user.username} ({self.rut})'



class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=12, blank=True, null=True)
    correo = models.EmailField()
    direccion = models.CharField(max_length=255, blank=True, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    productos = models.ManyToManyField('Producto', related_name='proveedores', blank=True)

    def __str__(self):
        return self.nombre
    

class Lote(models.Model):
    numero = models.CharField(max_length=50)
    fecha = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.numero} - {self.fecha}"
    

class Producto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=50)
    fecha = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def obtener_cantidad_total(self):
        return sum([
            detalle.cantidad for detalle in self.unidades.all().prefetch_related('detallelote_set')
        ])


class UnidadMedida(models.TextChoices):
    KILOGRAMO = 'kg', 'Kilogramo'
    UNIDAD = 'unidad', 'Unidad'
    CAJA = 'caja', 'Caja'

class ProductoUnidad(models.Model):
    producto = models.ForeignKey(Producto, related_name='unidades', on_delete=models.CASCADE)
    unidad_medida = models.CharField(max_length=10, choices=UnidadMedida.choices)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('producto', 'unidad_medida')  # evita duplicados

    def __str__(self):
        return f"{self.producto.nombre} - {self.get_unidad_medida_display()}"
    

class DetalleLote(models.Model):
    lote = models.ForeignKey(Lote, related_name="detalles", on_delete=models.CASCADE)
    producto_unidad = models.ForeignKey(ProductoUnidad, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.IntegerField()

    def __str__(self):
        return f"{self.producto_unidad} ({self.cantidad})"



class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='compras')
    activo = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras')
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('Pendiente', 'Pendiente'),
        ('Lista', 'Lista'),
        ('Cancelada', 'Cancelada'),
    ], default='Pendiente')

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor.nombre}"



class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    observaciones = models.TextField(blank=True, null=True)

    def subtotal(self):
        return 0

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Compra #{self.compra.id})"
    

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12)
    categoria = models.CharField(max_length=50)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre



class Merma(models.Model):
    producto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    lote = models.CharField(max_length=100)
    fecha = models.DateField(auto_now_add=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)


    def __str__(self):
        return self.producto





class Venta(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Venta #{self.id} - Cliente: {self.cliente.nombre}"