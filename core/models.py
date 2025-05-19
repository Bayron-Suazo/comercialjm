from django.db import models

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    lote_numero = models.IntegerField(null=True, blank=True)
    cantidad = models.IntegerField()
    tipo = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True) 
    activo = models.BooleanField(default=True)

    @property
    def lote(self):
        if self.lote_numero:
            return f"L-{self.lote_numero:03d}"
        return "Sin lote"

    def __str__(self):
        return self.nombre
    

class Lote(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    numero = models.CharField(max_length=50)
    fecha = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Lote {self.numero} - {self.producto.nombre}"


