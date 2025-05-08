from django import forms
from django.contrib.auth.models import User, Group
from registration.models import Profile
import random
import string

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    groups = forms.ModelMultipleChoiceField(
    label="Cargo",
    queryset=Group.objects.filter(name__in=["Administrador", "Empleado"]),
    widget=forms.CheckboxSelectMultiple,
    required=False
)

    class Meta:
        model = Profile
        fields = ['rut', 'telefono', 'fecha_nacimiento', 'direccion', 'sexo']


    sexo = forms.ChoiceField(
        label="Sexo",
        choices=[('M', 'Masculino'), ('F', 'Femenino')],
        widget=forms.RadioSelect
    )


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

        # Devuelve el perfil y la contraseña para que la vista la use
        return profile, password
    
