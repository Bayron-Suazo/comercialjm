from django import forms
from django.contrib.auth.models import User, Group


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