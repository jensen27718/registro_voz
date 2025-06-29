from django import forms
from .models import TipoProducto, Categoria, Producto, VariacionProducto, ValorAtributo

class TipoProductoForm(forms.ModelForm):
    class Meta:
        model = TipoProducto
        fields = ['nombre', 'descripcion', 'imagen_url']

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['tipo_producto', 'nombre', 'descripcion', 'imagen_url']

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['categoria', 'referencia', 'nombre', 'foto_url']

class VariacionProductoForm(forms.ModelForm):
    valores = forms.ModelMultipleChoiceField(queryset=ValorAtributo.objects.all())
    class Meta:
        model = VariacionProducto
        fields = ['producto', 'precio_base', 'valores']
