from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404, redirect
from datetime import datetime, timezone
from django.core.validators import MinValueValidator
from uuid import uuid4


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
    TIPO_CHOICES = [
        ('Fruta', 'Fruta'),
        ('Verdura', 'Verdura'),
        ('Otros', 'Otros'),
    ]
    UNIDAD_CHOICES = [
        ('kg', 'Kilogramo'),
        ('unidad', 'Unidad'),
        ('caja', 'Caja'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    unidad_medida = models.CharField(max_length=10, choices=UNIDAD_CHOICES)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    precio_caja = models.DecimalField(max_digits=10, decimal_places=2)
    contenido_por_caja = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    activo = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now_add=True)
    existencias = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Las existencias no pueden ser negativas"
    )

    lote = models.ForeignKey('Lote', on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def precio_por_unidad(self):
        if self.unidad_medida == 'caja':
            return self.precio_caja / self.contenido_por_caja
        return self.precio_venta

    def save(self, args, **kwargs):
        self.existencias = max(0, self.existencias)
        super().save(args, **kwargs)

    def str(self):
        return f"{self.nombre} ({self.unidad_medida})"


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
    

class DetalleLote(models.Model):
    lote = models.ForeignKey(Lote, related_name="detalles", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='detalles_lote')
    venta = models.ForeignKey('Venta', on_delete=models.CASCADE, related_name='detalles_lote', null=True, blank=True)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def str(self):
        return f"{self.producto} ({self.cantidad})"


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
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ventas', null=True, blank= True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(
        max_length=50,
        choices=[
            ('Efectivo', 'Efectivo'),
            ('Tarjeta', 'Tarjeta'),
            ('Transferencia', 'Transferencia')
        ],
        default='Efectivo'
    )

    def str(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y')}"
    

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='detalles', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    UNIDAD_CHOICES = [
        ('unidad', 'Unidad/Kg'),
        ('caja', 'Caja'),
    ]
    unidad = models.CharField(max_length=10, choices=UNIDAD_CHOICES, default='unidad') 

    def save(self, args, **kwargs):
        self.subtotal = self.precio = self.cantidad
        super().save(*args, **kwargs)

    def str(self):
        return f"{self.producto.nombre} x {self.cantidad}"



def generate_codigo():
    return str(uuid4())[:8]

class Cupon(models.Model):
    codigo = models.CharField(max_length=100, default=generate_codigo, blank=True, null=True)
    descuento = models.DecimalField(max_digits=5, decimal_places=2)
    activo = models.BooleanField(default=True)  # ← Nuevo campo
    usado = models.BooleanField(default=False)
    valido_hasta = models.DateField()
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"{self.codigo} ({self.descuento}%)"