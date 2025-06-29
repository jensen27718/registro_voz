from django import forms
from .models import TipoProducto, Categoria, Producto, VariacionProducto, ValorAtributo


class BaseStyledForm(forms.ModelForm):
    """Add Tailwind friendly classes to widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            cls = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"border rounded p-2 w-full {cls}".strip()

class TipoProductoForm(BaseStyledForm):
    class Meta:
        model = TipoProducto
        fields = ['nombre', 'descripcion', 'imagen_url']

class CategoriaForm(BaseStyledForm):
    class Meta:
        model = Categoria
        fields = ['tipo_producto', 'nombre', 'descripcion', 'imagen_url']

class ProductoForm(BaseStyledForm):
    class Meta:
        model = Producto
        fields = ['categoria', 'referencia', 'nombre', 'foto_url']

class VariacionProductoForm(BaseStyledForm):
    valores = forms.ModelMultipleChoiceField(
        queryset=ValorAtributo.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "border rounded p-2 w-full"}),
    )
    class Meta:
        model = VariacionProducto
        fields = ['producto', 'precio_base', 'valores']
