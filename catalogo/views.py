
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .forms import TipoProductoForm, CategoriaForm, ProductoForm, VariacionProductoForm
from .models import (
    Cliente, Administrador, TipoProducto, Categoria, Producto,
    AtributoDef, ValorAtributo, VariacionProducto, Promo,
    Pedido, PedidoItem
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
    cliente = Cliente.objects.filter(telefono=phone).order_by('-id').first()
    if not cliente:
        return HttpResponseNotFound()
    return JsonResponse({
        'phone': cliente.telefono,
        'name': cliente.nombre,
        'address': cliente.direccion,
        'city': cliente.ciudad,
    })


@csrf_exempt
@require_http_methods(["POST"])
def cliente_create(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')
    phone = payload.get('phone', '').strip()
    if not phone:
        return HttpResponseBadRequest('phone required')
    cliente = Cliente.objects.create(
        telefono=phone,
        nombre=payload.get('name', ''),
        direccion=payload.get('address', ''),
        ciudad=payload.get('city', ''),
    )
    return JsonResponse({
        'phone': cliente.telefono,
        'name': cliente.nombre,
        'address': cliente.direccion,
        'city': cliente.ciudad,
    })


@csrf_exempt
@require_http_methods(["POST"])
def pedido_create(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')

    cliente_data = payload.get('cliente')
    if not cliente_data:
        return HttpResponseBadRequest('cliente required')

    cliente, _ = Cliente.objects.get_or_create(
        telefono=cliente_data.get('phone'),
        defaults={
            'nombre': cliente_data.get('name', ''),
            'direccion': cliente_data.get('address', ''),
            'ciudad': cliente_data.get('city', ''),
        }
    )
    items = payload.get('items', [])
    pedido = Pedido.objects.create(cliente=cliente)
    for item in items:
        try:
            variacion = VariacionProducto.objects.get(id=item['variationId'])
        except VariacionProducto.DoesNotExist:
            continue
        PedidoItem.objects.create(
            pedido=pedido,
            variacion=variacion,
            cantidad=item.get('quantity', 1),
            precio_unitario=variacion.precio_base,
        )
    return JsonResponse({'id': pedido.id})


def admin_dashboard(request):
    section = request.GET.get('section', 'pedidos')
    tipo_form = TipoProductoForm(prefix='tipo')
    categoria_form = CategoriaForm(prefix='cat')
    producto_form = ProductoForm(prefix='prod')
    variacion_form = VariacionProductoForm(prefix='var')

    if request.method == 'POST':
        if 'tipo-nombre' in request.POST:
            tipo_form = TipoProductoForm(request.POST, prefix='tipo')
            if tipo_form.is_valid():
                tipo_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=tipo")
        if 'cat-nombre' in request.POST:
            categoria_form = CategoriaForm(request.POST, prefix='cat')
            if categoria_form.is_valid():
                categoria_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=categoria")
        if 'prod-nombre' in request.POST:
            producto_form = ProductoForm(request.POST, prefix='prod')
            if producto_form.is_valid():
                producto_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=producto")
        if 'var-precio_base' in request.POST:
            variacion_form = VariacionProductoForm(request.POST, prefix='var')
            if variacion_form.is_valid():
                variacion_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=variacion")

    pedidos = Pedido.objects.select_related('cliente').all().order_by('-fecha')
    from .models import EstadoPedido
    return render(request, 'catalogo/admin_dashboard.html', {
        'pedidos': pedidos,
        'tipo_form': tipo_form,
        'categoria_form': categoria_form,
        'producto_form': producto_form,
        'variacion_form': variacion_form,
        'estados': EstadoPedido.choices,
        'section': section,
    })


@require_http_methods(["POST"])
def actualizar_estado_pedido(request, pedido_id):
    estado = request.POST.get('estado')
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = estado
        pedido.save()
    except Pedido.DoesNotExist:
        return HttpResponseNotFound()
    return redirect('catalogo:admin_dashboard')

