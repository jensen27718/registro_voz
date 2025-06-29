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
        'tiposProducto': [
            {
                'id': tp.id,
                'nombre': tp.nombre,
                'descripcion': tp.descripcion,
                'imagen_url': tp.imagen_url,
            }
            for tp in TipoProducto.objects.all()
        ],
        'categorias': [
            {
                'id': c.id,
                'tipoProductoId': c.tipo_producto_id,
                'nombre': c.nombre,
                'imagen_url': c.imagen_url,
            }
            for c in Categoria.objects.all()
        ],
        'productos': [
            {
                'id': p.id,
                'categoriaId': p.categoria_id,
                'nombre': p.nombre,
                'foto_url': p.foto_url,
            }
            for p in Producto.objects.all()
        ],
        'atributoDefs': [
            {
                'id': a.id,
                'tipoProductoId': a.tipo_producto_id,
                'nombre': a.nombre,
            }
            for a in AtributoDef.objects.all()
        ],
        'valorAtributos': [
            {
                'id': v.id,
                'atributoDefId': v.atributo_def_id,
                'valor': v.valor,
                'display': v.display,
            }
            for v in ValorAtributo.objects.all()
        ],
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
