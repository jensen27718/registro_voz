from django import forms
from .models import (
    TipoProducto,
    Categoria,
    Producto,
    AtributoDef,
    ValorAtributo,
    VariacionProducto,
)



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


class AtributoDefForm(BaseStyledForm):

    class Meta:
        model = AtributoDef
        fields = ['tipo_producto', 'nombre']


class ValorAtributoForm(BaseStyledForm):

    def __init__(self, *args, **kwargs):
        """Show product type in attribute choices."""
        super().__init__(*args, **kwargs)
        field = self.fields["atributo_def"]
        field.label_from_instance = lambda obj: f"{obj.tipo_producto.nombre} - {obj.nombre}"

    class Meta:
        model = ValorAtributo
        fields = ['atributo_def', 'valor', 'display']


class VariacionProductoForm(BaseStyledForm):
    valores = forms.ModelMultipleChoiceField(
        queryset=ValorAtributo.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "border rounded p-2 w-full"}),
    )

    def __init__(self, *args, **kwargs):
        """Filtra los valores según el producto seleccionado."""
        super().__init__(*args, **kwargs)

        producto_id = None
        field_name = 'producto'
        if self.prefix:
            field_name = f'{self.prefix}-{field_name}'
        if self.data.get(field_name):
            producto_id = self.data.get(field_name)
        elif self.instance.pk:
            producto_id = self.instance.producto_id

        if producto_id:
            try:
                producto = Producto.objects.select_related('categoria__tipo_producto').get(pk=producto_id)
                tipo_id = producto.categoria.tipo_producto_id
                self.fields['valores'].queryset = ValorAtributo.objects.filter(
                    atributo_def__tipo_producto_id=tipo_id
                )
            except Producto.DoesNotExist:
                self.fields['valores'].queryset = ValorAtributo.objects.none()

    class Meta:
        model = VariacionProducto
        fields = ['producto', 'precio_base', 'valores']
