from django import forms
from django.contrib.auth.models import User, Group
from registration.models import Profile, Proveedor, Producto, Cliente, Merma, Compra, Lote, DetalleLote, ProductoUnidad, Venta, DetalleVenta
import re
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.forms import inlineformset_factory


class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'email', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Nombre'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Correo'}),
            'password': forms.PasswordInput(render_value=True, attrs={'placeholder': '********'}),
        }
        labels = {
            'first_name': 'Nombre',
            'email': 'Correo',
            'password': 'Contraseña'
        }


class CompraForm(forms.Form):
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.filter(estado=True),
        label="Proveedor"
    )

class DetalleCompraForm(forms.Form):
    producto_unidad = forms.ModelChoiceField(
        queryset=ProductoUnidad.objects.none(),  # Se actualizará dinámicamente
        label="Producto con Unidad"
    )
    cantidad = forms.IntegerField(min_value=1, label="Cantidad")
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label="Observaciones"
    )

class AprobarCompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['total']
        widgets = {
            'total': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'})
        }


# ------------------ CLIENTE ------------------

class ClienteForm(forms.ModelForm):
    CATEGORIAS = [
        ('mayorista', 'Mayorista'),
        ('frecuente', 'Frecuente'),
    ]

    categoria = forms.ChoiceField(choices=CATEGORIAS)

    class Meta:
        model = Cliente
        fields = ['nombre', 'rut', 'categoria', 'correo', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'input-estilo', 'id': 'nombre', 'autocomplete': 'off'}),
            'rut': forms.TextInput(attrs={'class': 'input-estilo', 'id': 'rut', 'autocomplete': 'off'}),
            'categoria': forms.Select(attrs={'class': 'input-estilo', 'id': 'categoria'}),
            'correo': forms.EmailInput(attrs={'class': 'input-estilo', 'id': 'correo', 'autocomplete': 'off'}),
            'telefono': forms.TextInput(attrs={'class': 'input-estilo', 'id': 'telefono', 'autocomplete': 'off'}),
            'direccion': forms.TextInput(attrs={'class': 'input-estilo', 'id': 'direccion', 'autocomplete': 'off'}),
        }



    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise ValidationError("El nombre solo debe contener letras.")
        return nombre

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')

        # Si estamos editando y el RUT no cambió, lo aceptamos directamente
        if self.instance and self.instance.pk and rut == self.instance.rut:
            return rut

        # Si es un nuevo registro o cambió el RUT, validamos normalmente
        if not validar_rut_chileno(rut):
            raise forms.ValidationError("rut_invalido_swal")

        return rut



    def clean_categoria(self):
        categoria = self.cleaned_data['categoria'].lower()
        if categoria not in ['mayorista', 'frecuente']:
            raise ValidationError("La categoría debe ser 'mayorista' o 'frecuente'")
        return categoria

    def clean_correo(self):
        correo = self.cleaned_data['correo']
        if "@" not in correo:
            raise ValidationError("El correo debe contener '@'.")
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono']
        if not re.match(r'^9\d{8}$', telefono):
            raise ValidationError("El teléfono debe comenzar con 9 y tener 9 dígitos en total.")
        return telefono
    
class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'metodo_pago']

class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto_unidad', 'cantidad']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        unidades = ProductoUnidad.objects.annotate(
            stock_total=Sum('detallelote__cantidad')
        ).order_by('producto__nombre', 'unidad_medida')

        # Mostrar nombre + unidad + stock entre paréntesis
        def get_label(pu):
            stock = pu.stock_total or 0
            return f"{pu.producto.nombre} - {pu.unidad_medida} ({int(stock)})"

        self.fields['producto_unidad'].queryset = unidades
        self.fields['producto_unidad'].label_from_instance = get_label


DetalleVentaFormSet = inlineformset_factory(
    Venta, DetalleVenta, form=DetalleVentaForm,
    extra=1, can_delete=True
)

def validar_rut_chileno(rut):
    try:
        cuerpo, dv_ingresado = rut.upper().split('-')
        cuerpo = cuerpo.strip()
        dv_ingresado = dv_ingresado.strip()

        suma = 0
        multiplo = 2
        for digito in reversed(cuerpo):
            suma += int(digito) * multiplo
            multiplo = 2 if multiplo == 7 else multiplo + 1  # ← corregido aquí

        dv_calculado = 11 - (suma % 11)
        if dv_calculado == 11:
            dv_calculado = '0'
        elif dv_calculado == 10:
            dv_calculado = 'K'
        else:
            dv_calculado = str(dv_calculado)

        return dv_calculado == dv_ingresado
    except Exception:
        return False