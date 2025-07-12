from django import template

register = template.Library()

@register.filter(name='estado_pedido_color')
def estado_pedido_color(estado_str):
    """
    Devuelve una clase de color de Tailwind CSS basada en el estado del pedido.
    """
    colores = {
        'PENDIENTE': 'bg-yellow-100 text-yellow-800',
        'PAGADO': 'bg-blue-100 text-blue-800',
        'EN_PROCESO': 'bg-indigo-100 text-indigo-800',
        'ENVIADO': 'bg-purple-100 text-purple-800',
        'ENTREGADO': 'bg-green-100 text-green-800',
        'CANCELADO': 'bg-red-100 text-red-800',
    }
    # Devuelve la clase correspondiente o una por defecto si el estado no se encuentra.

    return colores.get(estado_str, 'bg-gray-100 text-gray-800')


@register.filter(name='moneda')
def moneda(value):
    """Formatea valores numéricos como moneda colombiana."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    return "$%s" % ("{:,.0f}".format(value).replace(",", "."))

