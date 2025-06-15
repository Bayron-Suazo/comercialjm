from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404, redirect
from datetime import datetime, timezone
from django.core.validators import MinValueValidator

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
    fecha = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id} - {self.fecha}"
    

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

    def obtener_cantidades_por_unidad(self):
        cantidades = {}
        for unidad in self.unidades.all():
            total = sum(detalle.cantidad for detalle in unidad.detallelote_set.all())
            if total > 0:
                cantidades[unidad.get_unidad_medida_display()] = total
        return cantidades


class UnidadMedida(models.TextChoices):
    KILOGRAMO = 'kg', 'Kg'
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
    fecha = models.DateField(auto_now_add=True)  # Fecha en que se registra la merma
    producto_unidad = models.ForeignKey(ProductoUnidad, on_delete=models.CASCADE, related_name="mermas")
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True, related_name="mermas")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])  # Cantidad mínima 1
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])  # Precio manual ingresado
    motivo = models.TextField(blank=True, null=True)  # Descripción opcional de la merma

    def __str__(self):
        return f"Merma de {self.cantidad} {self.producto_unidad.get_unidad_medida_display()} de {self.producto_unidad.producto.nombre} en {self.fecha}"

    class Meta:
        ordering = ['-fecha']




class Venta(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Venta #{self.id} - Cliente: {self.cliente.nombre}"