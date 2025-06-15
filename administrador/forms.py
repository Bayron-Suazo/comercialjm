from django import forms
from django.contrib.auth.models import User, Group
from registration.models import Profile, Proveedor, Producto, Cliente, Merma, Compra, Lote, DetalleLote, ProductoUnidad, Venta, DetalleVenta
import random
import string
import re
from datetime import date
from itertools import cycle
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.db.models import Sum


# ------------------ AGREGAR USUARIO ------------------

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, label="Nombres",required=True)
    last_name = forms.CharField(max_length=30, label="Apellidos",required=True)
    groups = forms.ModelMultipleChoiceField(
        label="Cargo",
        queryset=Group.objects.filter(name__in=["Administrador", "Empleado"]),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    sexo = forms.ChoiceField(
        label="Sexo",
        choices=[('M', 'Masculino'), ('F', 'Femenino')],
        widget=forms.RadioSelect,
        required=True
    )

    class Meta:
        model = Profile
        fields = ['rut', 'telefono', 'fecha_nacimiento', 'direccion', 'sexo']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rut'].required = True
        self.fields['telefono'].required = True
        self.fields['fecha_nacimiento'].required = True
        self.fields['direccion'].required = True
        self.fields['sexo'].required = True

    # ---------------- VALIDACIONES ----------------

    def clean_first_name(self):
        nombres = self.cleaned_data.get('first_name', '').strip()
        partes = nombres.split()
        if len(partes) > 3:
            raise forms.ValidationError("Solo se permiten hasta 3 nombres.")
        if not all(p.isalpha() for p in partes):
            raise forms.ValidationError("Los nombres no deben contener números ni caracteres especiales.")
        return nombres

    def clean_last_name(self):
        apellidos = self.cleaned_data.get('last_name', '').strip()
        partes = apellidos.split()
        if len(partes) > 2:
            raise forms.ValidationError("Solo se permiten hasta 2 apellidos.")
        if not all(p.isalpha() for p in partes):
            raise forms.ValidationError("Los apellidos no deben contener números ni caracteres especiales.")
        return apellidos

    
    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '').strip()

        # Validación del formato XX.XXX.XXX-X
        if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', rut):
            raise forms.ValidationError('El RUT debe estar en el formato XX.XXX.XXX-X.')

        # Remover puntos y guión
        clean_rut = rut.replace(".", "").replace("-", "")

        num_part = clean_rut[:-1]
        dv = clean_rut[-1].upper()

        reversed_digits = list(map(int, reversed(num_part)))
        factors = cycle([2, 3, 4, 5, 6, 7])
        s = 0
        for d in reversed_digits:
            s += d * next(factors)

        mod = 11 - (s % 11)
        if mod == 11:
            verificador = '0'
        elif mod == 10:
            verificador = 'K'
        else:
            verificador = str(mod)

        if dv != verificador:
            raise forms.ValidationError('El RUT no es válido')

        if Profile.objects.filter(rut=rut).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un usuario con este RUT.')

        return rut

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        hoy = date.today()
        if fecha > hoy:
            raise forms.ValidationError("La fecha de nacimiento no puede ser posterior a hoy.")
        edad = hoy.year - fecha.year
        if edad > 100:
            raise forms.ValidationError("La edad no puede ser mayor a 100 años.")
        return fecha

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este correo electrónico.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        groups = cleaned_data.get('groups')
        if not groups:
            self.add_error('groups', "Debe seleccionar al menos un cargo.")
        return cleaned_data

    # ---------------- GENERAR Y GUARDAR USUARIO ----------------

    def generate_password(self, length=10):
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for _ in range(length))


    def save(self, commit=True):
        rut = self.cleaned_data['rut']
        password = self.generate_password()

        user = User(
            username=rut,
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        user.set_password(password)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data['groups'])

        profile = super().save(commit=False)
        profile.user = user
        if commit:
            profile.save()
            profile.groups.set(self.cleaned_data['groups'])

        return profile, password
    


# ------------------ CARGA MASIVA ------------------
 
 
    
class CargaMasivaUsuariosForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel", required=True)



# ------------------ EDITAR USUARIO ------------------



class EditUserProfileForm(forms.ModelForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    group = forms.ModelMultipleChoiceField(
        label="Cargo",
        queryset=Group.objects.filter(name__in=["Administrador", "Empleado"]),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    sexo = forms.ChoiceField(
        label="Sexo",
        choices=[('M', 'Masculino'), ('F', 'Femenino')],
        widget=forms.RadioSelect
    )

    class Meta:
        model = Profile
        fields = ['rut', 'telefono', 'fecha_nacimiento', 'direccion', 'sexo']
        widgets = {
            'fecha_nacimiento': forms.DateInput(
            attrs={'type': 'date'},
            format='%Y-%m-%d'
        )}

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)

        if self.user_instance:
            self.fields['email'].initial = self.user_instance.email
            self.fields['first_name'].initial = self.user_instance.first_name
            self.fields['last_name'].initial = self.user_instance.last_name
            self.fields['group'].initial = self.user_instance.groups.all()

        # Hacer que todos los campos del modelo sean requeridos
        self.fields['rut'].required = True
        self.fields['telefono'].required = True
        self.fields['fecha_nacimiento'].required = True
        self.fields['direccion'].required = True
        self.fields['sexo'].required = True

    # ---------------- VALIDACIONES ----------------

    def clean_first_name(self):
        nombres = self.cleaned_data.get('first_name', '').strip()
        partes = nombres.split()
        if len(partes) > 3:
            raise forms.ValidationError("Solo se permiten hasta 3 nombres.")
        if not all(p.isalpha() for p in partes):
            raise forms.ValidationError("Los nombres no deben contener números ni caracteres especiales.")
        return nombres

    def clean_last_name(self):
        apellidos = self.cleaned_data.get('last_name', '').strip()
        partes = apellidos.split()
        if len(partes) > 2:
            raise forms.ValidationError("Solo se permiten hasta 2 apellidos.")
        if not all(p.isalpha() for p in partes):
            raise forms.ValidationError("Los apellidos no deben contener números ni caracteres especiales.")
        return apellidos

    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '').strip()

        # Validación del formato XX.XXX.XXX-X
        if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', rut):
            raise forms.ValidationError('El RUT debe estar en el formato XX.XXX.XXX-X.')

        clean_rut = rut.replace(".", "").replace("-", "")
        num_part = clean_rut[:-1]
        dv = clean_rut[-1].upper()

        reversed_digits = list(map(int, reversed(num_part)))
        factors = cycle([2, 3, 4, 5, 6, 7])
        s = sum(d * next(factors) for d in reversed_digits)

        mod = 11 - (s % 11)
        verificador = '0' if mod == 11 else 'K' if mod == 10 else str(mod)

        if dv != verificador:
            raise forms.ValidationError('El RUT no es válido')

        if Profile.objects.filter(rut=rut).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un usuario con este RUT.')

        return rut

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        hoy = date.today()
        if fecha > hoy:
            raise forms.ValidationError("La fecha de nacimiento no puede ser posterior a hoy.")
        edad = hoy.year - fecha.year
        if edad > 100:
            raise forms.ValidationError("La edad no puede ser mayor a 100 años.")
        return fecha

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email=email).exclude(pk=self.user_instance.pk).exists():
            raise forms.ValidationError("Ya existe un usuario con este correo electrónico.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get('group')
        if not group:
            self.add_error('group', "Debe seleccionar al menos un cargo.")
        return cleaned_data

    # ---------------- GUARDADO ----------------

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = self.user_instance

        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            user.groups.set(self.cleaned_data['group'])
            profile.user = user
            profile.save()

        return profile
    


# ------------------ PERFIL USUARIO ------------------


    
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



# ------------------ CREAR PROVEEDOR ------------------



class CrearProveedorForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre del proveedor",
        max_length=100,
        required=True
    )
    rut = forms.CharField(
        label="RUT",
        max_length=12,
        required=True
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=12,
        required=False
    )
    correo = forms.EmailField(
        label="Correo electrónico",
        required=True
    )
    direccion = forms.CharField(
        label="Dirección",
        max_length=255,
        required=False
    )

    class Meta:
        model = Proveedor
        fields = ['nombre', 'rut', 'telefono', 'correo', 'direccion']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        partes = nombre.split()
        if len(partes) > 2:
            raise forms.ValidationError("Solo se permiten hasta 2 nombres.")
        if not all(p.isalpha() for p in partes):
            raise forms.ValidationError("El nombre no permite números ni caracteres especiales.")
        return nombre

    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '').strip()

        # Validación del formato XX.XXX.XXX-X
        if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', rut):
            raise forms.ValidationError('El RUT debe estar en el formato XX.XXX.XXX-X.')

        # Remover puntos y guión
        clean_rut = rut.replace(".", "").replace("-", "")

        num_part = clean_rut[:-1]
        dv = clean_rut[-1].upper()

        if not num_part.isdigit():
            raise forms.ValidationError("El RUT contiene caracteres inválidos.")

        reversed_digits = list(map(int, reversed(num_part)))
        factors = cycle([2, 3, 4, 5, 6, 7])
        s = sum(d * next(factors) for d in reversed_digits)

        mod = 11 - (s % 11)
        verificador = '0' if mod == 11 else 'K' if mod == 10 else str(mod)

        if dv != verificador:
            raise forms.ValidationError('El RUT no es válido.')

        if Proveedor.objects.filter(rut=rut).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un proveedor con este RUT.')

        return rut

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').strip()
        if Proveedor.objects.filter(correo=correo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un proveedor con este correo.")
        return correo



class EditarProveedorForm(CrearProveedorForm):

    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '').strip()

        # Validación del formato XX.XXX.XXX-X
        if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', rut):
            raise forms.ValidationError('El RUT debe estar en el formato XX.XXX.XXX-X.')

        # Remover puntos y guión
        clean_rut = rut.replace(".", "").replace("-", "")

        num_part = clean_rut[:-1]
        dv = clean_rut[-1].upper()

        if not num_part.isdigit():
            raise forms.ValidationError("El RUT contiene caracteres inválidos.")

        reversed_digits = list(map(int, reversed(num_part)))
        factors = cycle([2, 3, 4, 5, 6, 7])
        s = sum(d * next(factors) for d in reversed_digits)

        mod = 11 - (s % 11)
        verificador = '0' if mod == 11 else 'K' if mod == 10 else str(mod)

        if dv != verificador:
            raise forms.ValidationError('El RUT no es válido.')

        # Validar unicidad excluyendo al proveedor actual
        if Proveedor.objects.filter(rut=rut).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un proveedor con este RUT.')

        return rut

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').strip()
        if Proveedor.objects.filter(correo=correo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un proveedor con este correo.")
        return correo
    


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
    class Meta:
        model = Cliente
        fields = ['nombre', 'rut', 'categoria', 'correo', 'telefono']

from django import forms
from registration .models import Producto, ProductoUnidad, UnidadMedida
from django.forms import inlineformset_factory

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'tipo']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Producto.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe este producto.")
        return nombre
    
class EditarProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'tipo']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        qs = Producto.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe este producto.")
        return nombre
    
class ProductoUnidadForm(forms.ModelForm):
    class Meta:
        model = ProductoUnidad
        fields = ['unidad_medida', 'precio']
        widgets = {
            'unidad_medida': forms.Select(choices=UnidadMedida.choices),
            'precio': forms.NumberInput(attrs={'step': '0.01'}),
        }

ProductoUnidadFormSet = inlineformset_factory(
    Producto,
    ProductoUnidad,
    form=ProductoUnidadForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DetalleLoteForm(forms.ModelForm):
    class Meta:
        model = DetalleLote
        fields = ['producto_unidad', 'cantidad']
        widgets = {
            'producto_unidad': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a 0.")
        return cantidad

from django.forms import BaseModelFormSet, ValidationError

class BaseDetalleLoteFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        productos_unidad = []

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if not form.cleaned_data:
                raise ValidationError("Por favor, completa todos los campos.")

            producto_unidad = form.cleaned_data.get('producto_unidad')
            cantidad = form.cleaned_data.get('cantidad')

            if producto_unidad is None:
                raise ValidationError("Selecciona un producto con unidad.")
            if cantidad is None or cantidad <= 0:
                raise ValidationError("La cantidad debe ser mayor que cero.")

            if producto_unidad in productos_unidad:
                raise ValidationError("No se pueden repetir productos con la misma unidad en el detalle del lote.")
            productos_unidad.append(producto_unidad)

DetalleLoteFormSet = modelformset_factory(
    DetalleLote,
    form=DetalleLoteForm,
    formset=BaseDetalleLoteFormSet,
    extra=1,
    can_delete=True,
)

 
class MermaForm(forms.ModelForm):
    class Meta:
        model = Merma
        fields = ['producto_unidad', 'lote', 'cantidad', 'precio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto_unidad'].queryset = ProductoUnidad.objects.filter(
            detallelote__cantidad__gt=0
        ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        producto_unidad = cleaned_data.get('producto_unidad')
        lote = cleaned_data.get('lote')
        cantidad = cleaned_data.get('cantidad')

        if producto_unidad and lote:
            # Buscar los lotes asociados con este producto_unidad (stock > 0)
            lotes_disponibles = DetalleLote.objects.filter(
                producto_unidad=producto_unidad,
                cantidad__gt=0
            ).values_list('lote__id', 'lote__fecha')

            try:
                detalle = DetalleLote.objects.get(
                    producto_unidad=producto_unidad,
                    lote=lote
                )
            except DetalleLote.DoesNotExist:
                # Construir mensaje con lotes disponibles
                if lotes_disponibles.exists():
                    lotes_str = ", ".join(
                        [f"ID {lote_id} (fecha {fecha})" for lote_id, fecha in lotes_disponibles]
                    )
                    raise forms.ValidationError(
                        f"El lote seleccionado no corresponde al producto y unidad elegidos. "
                        f"Lotes disponibles para el producto/unidad seleccionado: {lotes_str}."
                    )
                else:
                    raise forms.ValidationError(
                        "El lote seleccionado no corresponde al producto y unidad elegidos. "
                        "No hay lotes disponibles para el producto/unidad seleccionado."
                    )

            if cantidad is not None and cantidad > detalle.cantidad:
                raise forms.ValidationError(
                    f"La cantidad ingresada ({cantidad}) supera el stock disponible del lote ({detalle.cantidad})."
                )

class MotivoMermaForm(forms.Form):
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Motivo de la merma'}),
        label='Motivo',
        required=True
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


class ClienteForm(forms.ModelForm):
    CATEGORIAS = [
        ('mayorista', 'Mayorista'),
        ('frecuente', 'Frecuente'),
        ('ambos', 'Ambos'),
    ]

    categoria = forms.ChoiceField(choices=CATEGORIAS)

    class Meta:
        model = Cliente
        fields = ['nombre', 'rut', 'categoria', 'correo', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'input-estilo', 'id': 'nombre', 'autocomplete': 'off'}),
            'rut': forms.TextInput(attrs={'class': 'input-estilo', 'id': 'rut', 'autocomplete': 'off'}),
            'categoria': forms.Select(attrs={'class': 'input-estilo', 'id': 'categoria'}),
            'correo': forms.EmailInput(attrs={'class': 'input-estilo', 'id': 'correo', 'autocomplete': 'off'}),
            'telefono': forms.TextInput(attrs={'class': 'input-estilo', 'id': 'telefono', 'autocomplete': 'off'}),
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
        if categoria not in ['mayorista', 'frecuente', 'ambos']:
            raise ValidationError("La categoría debe ser 'mayorista', 'frecuente' o 'ambos'.")
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
    
class CargaMasivaProveedorForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel", required=True)

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'metodo_pago']

class DetalleVentaForm(forms.ModelForm):
    producto_unidad = forms.ModelChoiceField(
        queryset=ProductoUnidad.objects.none(),
        label="Producto"
    )

    class Meta:
        model = DetalleVenta
        fields = ['producto_unidad', 'cantidad']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ordenar por producto__nombre y unidad_medida según orden personalizado
        # Primero obtenemos todos los ProductoUnidad ordenados por producto__nombre
        # y luego ordenamos en Python según unidad_medida.

        unidades = ProductoUnidad.objects.select_related('producto').all()

        # Diccionario para asignar prioridad al orden de unidad
        orden_unidad = {'caja': 1, 'kg': 2, 'unidad': 3}

        # Calcular stock para cada producto_unidad (sumar cantidad en DetalleLote)
        stock_map = {}
        for pu in unidades:
            total_stock = DetalleLote.objects.filter(
                producto_unidad=pu, cantidad__gt=0, lote__activo=True
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            stock_map[pu.id] = total_stock

        # Ordenar la lista de objetos ProductoUnidad
        unidades = sorted(
            unidades,
            key=lambda pu: (
                pu.producto.nombre.lower(),
                orden_unidad.get(pu.unidad_medida.lower(), 99)
            )
        )

        # Construir lista de tuples para las opciones con stock en el label
        opciones = []
        for pu in unidades:
            nombre_opcion = f"{pu.producto.nombre} ({pu.unidad_medida}) - Stock: {stock_map.get(pu.id, 0)}"
            opciones.append((pu.id, nombre_opcion))

        # Finalmente asignar el queryset vacío y opciones personalizadas al campo
        self.fields['producto_unidad'].choices = opciones

DetalleVentaFormSet = inlineformset_factory(
    Venta, DetalleVenta, form=DetalleVentaForm,
    extra=1, can_delete=True
)