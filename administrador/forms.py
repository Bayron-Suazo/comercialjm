from django import forms
from django.contrib.auth.models import User, Group
from registration.models import Profile
import random
import string
import re
from datetime import date
from itertools import cycle


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, label="Nombres")
    last_name = forms.CharField(max_length=30, label="Apellidos")
    groups = forms.ModelMultipleChoiceField(
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
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'})
        }

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
    
class CargaMasivaUsuariosForm(forms.Form):
    archivo = forms.FileField()


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