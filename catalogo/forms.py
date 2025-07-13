from django import forms
from .models import (
    TipoProducto,
    Categoria,
    Producto,
    AtributoDef,
    ValorAtributo,
    VariacionProducto,
    VariacionBase,
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
        """Filter values by the selected product and group them by attribute."""
        super().__init__(*args, **kwargs)

        producto_id = None
        field_name = 'producto'
        if self.prefix:
            field_name = f'{self.prefix}-{field_name}'
        if self.data.get(field_name):
            producto_id = self.data.get(field_name)
        elif self.instance.pk:
            producto_id = self.instance.producto_id
        elif self.initial.get('producto'):
            producto_id = self.initial.get('producto')

        if producto_id:
            try:
                producto = Producto.objects.select_related('categoria__tipo_producto').get(pk=producto_id)
                tipo_id = producto.categoria.tipo_producto_id
                valores_qs = ValorAtributo.objects.filter(
                    atributo_def__tipo_producto_id=tipo_id
                ).select_related('atributo_def')
                self.fields['valores'].queryset = valores_qs
                atributos = (
                    AtributoDef.objects.filter(tipo_producto_id=tipo_id)
                    .order_by('nombre')
                )
                grupos = {a.nombre: [] for a in atributos}
                for v in valores_qs:
                    grupos[v.atributo_def.nombre].append((v.id, v.valor))
                choices = [(a.nombre, grupos[a.nombre]) for a in atributos]
                self.fields['valores'].choices = choices
                self.fields['valores'].widget.choices = choices
            except Producto.DoesNotExist:
                self.fields['valores'].queryset = ValorAtributo.objects.none()

    class Meta:
        model = VariacionProducto
        fields = ['producto', 'precio_base', 'valores']


class VariacionBaseForm(BaseStyledForm):
    valores = forms.ModelMultipleChoiceField(
        queryset=ValorAtributo.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "border rounded p-2 w-full"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tipo_id = None
        field_name = 'tipo_producto'
        if self.prefix:
            field_name = f'{self.prefix}-{field_name}'
        if self.data.get(field_name):
            tipo_id = self.data.get(field_name)
        elif self.instance.pk:
            tipo_id = self.instance.tipo_producto_id
        elif self.initial.get('tipo_producto'):
            tipo_id = self.initial.get('tipo_producto')

        if tipo_id:
            valores_qs = ValorAtributo.objects.filter(
                atributo_def__tipo_producto_id=tipo_id
            ).select_related('atributo_def')
            self.fields['valores'].queryset = valores_qs
            atributos = (
                AtributoDef.objects.filter(tipo_producto_id=tipo_id)
                .order_by('nombre')
            )
            grupos = {a.nombre: [] for a in atributos}
            for v in valores_qs:
                grupos[v.atributo_def.nombre].append((v.id, v.valor))
            choices = [(a.nombre, grupos[a.nombre]) for a in atributos]
            self.fields['valores'].choices = choices
            self.fields['valores'].widget.choices = choices

    class Meta:
        model = VariacionBase
        fields = ['tipo_producto', 'precio_base', 'valores']


class CargaMasivaForm(BaseStyledForm):
    tipo_producto = forms.ModelChoiceField(queryset=TipoProducto.objects.all())
    heredar_variaciones = forms.BooleanField(required=False)
    archivo = forms.FileField()

    class Meta:
        model = Producto
        fields = []



class CargaImagenForm(BaseStyledForm):
    tipo_producto = forms.ModelChoiceField(queryset=TipoProducto.objects.all())
    heredar_variaciones = forms.BooleanField(required=False)
    


    class Meta:
        model = Producto
        fields = []


