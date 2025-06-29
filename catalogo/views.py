
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .models import (
    Cliente, Administrador, TipoProducto, Categoria, Producto,
    AtributoDef, ValorAtributo, VariacionProducto, Promo
)

WHATSAPP_NUMBER = '573001234567'


def build_catalog_data():
    return {
        'tiposProducto': list(TipoProducto.objects.values('id', 'nombre', 'descripcion')),
        'categorias': list(Categoria.objects.values('id', 'tipo_producto_id', 'nombre', 'imagen_url')),
        'productos': list(Producto.objects.values('id', 'categoria_id', 'nombre', 'foto_url')),
        'atributoDefs': list(AtributoDef.objects.values('id', 'tipo_producto_id', 'nombre')),
        'valorAtributos': list(ValorAtributo.objects.values('id', 'atributo_def_id', 'valor', 'display')),
        'variacionesProducto': [
            {
                'id': v.id,
                'productoId': v.producto_id,
                'precioBase': float(v.precio_base),
                'valorAtributoIds': list(v.valores.values_list('id', flat=True)),
            }
            for v in VariacionProducto.objects.all().prefetch_related('valores')
        ],
        'promos': list(Promo.objects.values('id', 'codigo', 'descripcion', 'porcentaje', 'fecha_inicio', 'fecha_fin', 'activo')),
    }


def catalogo_view(request):
    data = build_catalog_data()
    context = {
        'initial_data': json.dumps(data, default=str),
        'whatsapp_number': WHATSAPP_NUMBER,
    }
    return render(request, 'catalogo/catalogo.html', context)


@require_http_methods(["GET"])
def cliente_detail(request):
    phone = request.GET.get('phone')
    if not phone:
        return HttpResponseBadRequest('phone required')
    try:
        cliente = Cliente.objects.get(telefono=phone)
    except Cliente.DoesNotExist:
        return HttpResponseNotFound()
    return JsonResponse({
        'phone': cliente.telefono,
        'name': cliente.nombre,
        'address': cliente.direccion,
        'city': cliente.ciudad,
    })


@require_http_methods(["POST"])
def cliente_create(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')
    phone = payload.get('phone', '').strip()
    if not phone:
        return HttpResponseBadRequest('phone required')
    cliente, _ = Cliente.objects.get_or_create(telefono=phone)
    cliente.nombre = payload.get('name', cliente.nombre)
    cliente.direccion = payload.get('address', cliente.direccion)
    cliente.ciudad = payload.get('city', cliente.ciudad)
    cliente.save()
    return JsonResponse({
        'phone': cliente.telefono,
        'name': cliente.nombre,
        'address': cliente.direccion,
        'city': cliente.ciudad,
    })

