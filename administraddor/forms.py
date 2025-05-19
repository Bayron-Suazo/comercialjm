from django import forms
from .models import Merma, Producto

class MermaForm(forms.ModelForm):
    class Meta:
        model = Merma
        fields = ['producto', 'cantidad', 'precio']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)

    def clean_producto(self):
        producto = self.cleaned_data.get('producto')
        if not producto.activo:
            raise forms.ValidationError("Este producto no está activo en el inventario")
        return producto

