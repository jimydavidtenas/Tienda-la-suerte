from django import forms
from .models import Cliente, Venta, ResultadoSorteo

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'direccion', 'fecha_nacimiento']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'sorteo', 'numero_apostado', 'monto', 'numero_sorteo_dia']
        widgets = {
            'numero_apostado': forms.NumberInput(attrs={'min': 0, 'max': 99}),
            'monto': forms.NumberInput(attrs={'step': '0.01'}),
        }

class ResultadoSorteoForm(forms.ModelForm):
    class Meta:
        model = ResultadoSorteo
        fields = ['sorteo', 'fecha', 'numero_ganador', 'numero_sorteo_dia']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'numero_ganador': forms.NumberInput(attrs={'min': 0, 'max': 99}),
        }