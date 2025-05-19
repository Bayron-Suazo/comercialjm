from django.db import models
from core.models import Producto

class Merma(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio = models.CharField(max_length=20)
    fecha = models.DateField()
    lote = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.producto.nombre} - {self.lote}"