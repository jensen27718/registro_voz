# catalogo/views.py

import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

# --- IMPORTACIONES PARA AUTENTICACIÓN Y PDF (LÍNEA CORREGIDA) ---
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
# ---------------------------------------------

from .forms import (
    TipoProductoForm,
    CategoriaForm,
    ProductoForm,
    VariacionProductoForm,
    AtributoDefForm,
    ValorAtributoForm,
)
from .models import (
    Cliente, Administrador, TipoProducto, Categoria, Producto,
    AtributoDef, ValorAtributo, VariacionProducto, Promo,
    Carrito, CarritoItem,
    Pedido, PedidoItem, EstadoPedido
)

WHATSAPP_NUMBER = '573212165252'


def build_catalog_data():
    """Construye el diccionario de datos inicial para el frontend."""
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
    """Vista principal que renderiza la aplicación de catálogo."""
    data = build_catalog_data()
    context = {
        'initial_data': json.dumps(data, default=str),
        'whatsapp_number': WHATSAPP_NUMBER,
    }
    return render(request, 'catalogo/catalogo.html', context)


@require_http_methods(["GET"])
def cliente_detail(request):
    """Obtiene los detalles de un cliente por su número de teléfono."""
    phone = request.GET.get('phone')
    if not phone:
        return HttpResponseBadRequest('phone required')
    cliente = Cliente.objects.filter(telefono=phone).order_by('-id').first()
    if not cliente:
        return HttpResponseNotFound('Client not found')
    return JsonResponse({
        'phone': cliente.telefono,
        'name': cliente.nombre,
        'address': cliente.direccion,
        'city': cliente.ciudad,
    })


@csrf_exempt
@require_http_methods(["POST"])
def cliente_create(request):
    """Crea un nuevo cliente o actualiza uno existente."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')
    phone = payload.get('phone', '').strip()
    if not phone:
        return HttpResponseBadRequest('phone required')

    cliente, _ = Cliente.objects.update_or_create(
        telefono=phone,
        defaults={
            'nombre': payload.get('name', ''),
            'direccion': payload.get('address', ''),
            'ciudad': payload.get('city', ''),
        }
    )

    return JsonResponse({
        'phone': cliente.telefono,
        'name': cliente.nombre,
        'address': cliente.direccion,
        'city': cliente.ciudad,
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def cart_view(request):
    """API para obtener (GET) y guardar (POST) el carrito de un cliente."""
    if request.method == 'GET':
        phone = request.GET.get('phone')
        if not phone:
            return HttpResponseBadRequest('phone required')
        try:
            cliente = Cliente.objects.get(telefono=phone)
            carrito, _ = Carrito.objects.get_or_create(cliente=cliente)
            
            items = []
            for item in carrito.items.select_related('variacion__producto').prefetch_related('variacion__valores__atributo_def').all():
                atributos = [{'nombre': v.atributo_def.nombre, 'valor': v.valor} for v in item.variacion.valores.all()]
                items.append({
                    'variationId': item.variacion.id,
                    'productoId': item.variacion.producto.id,
                    'name': item.variacion.producto.nombre,
                    'image': item.variacion.producto.foto_url,
                    'priceBase': float(item.variacion.precio_base),
                    'quantity': item.cantidad,
                    'atributos': atributos,
                })
            return JsonResponse({'items': items, 'appliedPromoCode': None})
        except Cliente.DoesNotExist:
            return HttpResponseNotFound('Client not found')

    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            phone = payload.get('phone')
            if not phone:
                return HttpResponseBadRequest('phone required')
            with transaction.atomic():
                cliente = Cliente.objects.get(telefono=phone)
                carrito, _ = Carrito.objects.get_or_create(cliente=cliente)
                
                carrito.items.all().delete()
                
                items_data = payload.get('items', [])
                for item_data in items_data:
                    try:
                        variacion = VariacionProducto.objects.get(id=item_data.get('variationId'))
                        cantidad = int(item_data.get('quantity', 1))
                        if cantidad > 0:
                            CarritoItem.objects.create(carrito=carrito, variacion=variacion, cantidad=cantidad)
                    except (VariacionProducto.DoesNotExist, ValueError):
                        continue
            return JsonResponse({'status': 'ok'})
        except Cliente.DoesNotExist:
            return HttpResponseNotFound('Client not found')
        except Exception as e:
            return HttpResponseBadRequest(f'Error syncing cart: {e}')


@csrf_exempt
@require_http_methods(["POST"])
def pedido_create(request):
    """Crea un pedido a partir del carrito de un cliente guardado en la DB."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')

    cliente_data = payload.get('cliente')
    if not cliente_data or not cliente_data.get('phone'):
        return HttpResponseBadRequest('cliente con phone es requerido')
    
    try:
        cliente = Cliente.objects.get(telefono=cliente_data['phone'])
    except Cliente.DoesNotExist:
        return HttpResponseNotFound('Cliente no encontrado. No se puede crear el pedido.')

    try:
        carrito = Carrito.objects.get(cliente=cliente)
        if not carrito.items.exists():
            return HttpResponseBadRequest('No se puede crear un pedido de un carrito vacío.')

        with transaction.atomic():
            promo_code = payload.get('promoCode')
            if promo_code:
                promo = Promo.objects.filter(codigo=promo_code, activo=True).first()
                if promo and promo.es_valido():
                    carrito.promos.set([promo])
                else:
                    carrito.promos.clear()
            else:
                carrito.promos.clear()
            
            pedido = Pedido.crear_desde_carrito(carrito)
            
            carrito.items.all().delete()
            carrito.promos.clear()
            
    except Carrito.DoesNotExist:
        return HttpResponseBadRequest('El cliente no tiene un carrito activo.')
    except Exception as e:
        return HttpResponseBadRequest(f"Ocurrió un error inesperado: {e}")

    return JsonResponse({'id': pedido.id})


@staff_member_required
def admin_dashboard(request):
    """Panel de administración del catálogo, protegido por login de staff."""
    section = request.GET.get('section', 'pedidos')
    edit_tipo = request.GET.get('edit_tipo')
    edit_cat = request.GET.get('edit_cat')
    edit_prod = request.GET.get('edit_prod')
    edit_var = request.GET.get('edit_var')
    edit_atr = request.GET.get('edit_atr')
    edit_val = request.GET.get('edit_val')

    tipo_form = TipoProductoForm(prefix='tipo', instance=TipoProducto.objects.get(id=edit_tipo) if edit_tipo else None)
    categoria_form = CategoriaForm(prefix='cat', instance=Categoria.objects.get(id=edit_cat) if edit_cat else None)
    producto_form = ProductoForm(prefix='prod', instance=Producto.objects.get(id=edit_prod) if edit_prod else None)
    variacion_form = VariacionProductoForm(prefix='var', instance=VariacionProducto.objects.get(id=edit_var) if edit_var else None)
    atributo_form = AtributoDefForm(prefix='atr', instance=AtributoDef.objects.get(id=edit_atr) if edit_atr else None)
    valor_form = ValorAtributoForm(prefix='val', instance=ValorAtributo.objects.get(id=edit_val) if edit_val else None)

    if request.method == 'POST':
        # eliminaciones
        if 'delete_tipo' in request.POST:
            TipoProducto.objects.filter(id=request.POST['delete_tipo']).delete()
            return redirect(f"{reverse('catalogo:admin_dashboard')}?section=tipo")
        if 'delete_cat' in request.POST:
            Categoria.objects.filter(id=request.POST['delete_cat']).delete()
            return redirect(f"{reverse('catalogo:admin_dashboard')}?section=categoria")
        if 'delete_prod' in request.POST:
            Producto.objects.filter(id=request.POST['delete_prod']).delete()
            return redirect(f"{reverse('catalogo:admin_dashboard')}?section=producto")
        if 'delete_var' in request.POST:
            VariacionProducto.objects.filter(id=request.POST['delete_var']).delete()
            return redirect(f"{reverse('catalogo:admin_dashboard')}?section=variacion")
        if 'delete_atr' in request.POST:
            AtributoDef.objects.filter(id=request.POST['delete_atr']).delete()
            return redirect(f"{reverse('catalogo:admin_dashboard')}?section=atributo")
        if 'delete_val' in request.POST:
            ValorAtributo.objects.filter(id=request.POST['delete_val']).delete()
            return redirect(f"{reverse('catalogo:admin_dashboard')}?section=valor")

        # creaciones/ediciones
        if 'tipo-nombre' in request.POST:
            instance = TipoProducto.objects.get(id=edit_tipo) if edit_tipo else None
            tipo_form = TipoProductoForm(request.POST, prefix='tipo', instance=instance)
            if tipo_form.is_valid():
                tipo_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=tipo")
        if 'cat-nombre' in request.POST:
            instance = Categoria.objects.get(id=edit_cat) if edit_cat else None
            categoria_form = CategoriaForm(request.POST, prefix='cat', instance=instance)
            if categoria_form.is_valid():
                categoria_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=categoria")
        if 'prod-nombre' in request.POST:
            instance = Producto.objects.get(id=edit_prod) if edit_prod else None
            producto_form = ProductoForm(request.POST, prefix='prod', instance=instance)
            if producto_form.is_valid():
                producto_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=producto")
        if 'var-precio_base' in request.POST:
            instance = VariacionProducto.objects.get(id=edit_var) if edit_var else None
            variacion_form = VariacionProductoForm(request.POST, prefix='var', instance=instance)
            if variacion_form.is_valid():
                variacion_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=variacion")
        if 'atr-nombre' in request.POST:
            instance = AtributoDef.objects.get(id=edit_atr) if edit_atr else None
            atributo_form = AtributoDefForm(request.POST, prefix='atr', instance=instance)
            if atributo_form.is_valid():
                atributo_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=atributo")
        if 'val-valor' in request.POST:
            instance = ValorAtributo.objects.get(id=edit_val) if edit_val else None
            valor_form = ValorAtributoForm(request.POST, prefix='val', instance=instance)
            if valor_form.is_valid():
                valor_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=valor")

    pedidos = (
        Pedido.objects.select_related('cliente')
        .prefetch_related(
            'items__variacion__producto',
            'items__variacion__valores__atributo_def'
        )
        .all()
        .order_by('-fecha')
    )
    clientes = Cliente.objects.all().order_by('nombre')
    tipos = TipoProducto.objects.all().order_by('nombre')
    categorias = Categoria.objects.select_related('tipo_producto').order_by('tipo_producto__nombre', 'nombre')
    productos = Producto.objects.select_related('categoria__tipo_producto').order_by('categoria__nombre', 'nombre')
    variaciones = (
        VariacionProducto.objects.select_related('producto__categoria__tipo_producto')
        .prefetch_related('valores__atributo_def')
        .all()
    )
    atributos = AtributoDef.objects.select_related('tipo_producto').order_by('tipo_producto__nombre', 'nombre')
    valores = ValorAtributo.objects.select_related('atributo_def__tipo_producto').order_by('atributo_def__nombre', 'valor')

    return render(request, 'catalogo/admin_dashboard.html', {
        'pedidos': pedidos,
        'tipo_form': tipo_form,
        'categoria_form': categoria_form,
        'producto_form': producto_form,
        'variacion_form': variacion_form,
        'atributo_form': atributo_form,
        'valor_form': valor_form,
        'clientes': clientes,
        'tipos': tipos,
        'categorias': categorias,
        'productos': productos,
        'variaciones': variaciones,
        'atributos': atributos,
        'valores': valores,
        'estados': EstadoPedido.choices,
        'section': section,
    })


@staff_member_required
@require_http_methods(["POST"])
def actualizar_estado_pedido(request, pedido_id):
    """Actualiza el estado de un pedido."""
    estado = request.POST.get('estado')
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        if estado in [choice[0] for choice in EstadoPedido.choices]:
            pedido.estado = estado
            pedido.save()
    except Pedido.DoesNotExist:
        return HttpResponseNotFound()
    return redirect('catalogo:admin_dashboard')


def render_to_pdf(template_src, context_dict={}):
    """Función auxiliar para renderizar un template HTML a un objeto PDF."""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

@staff_member_required
def generar_pedido_pdf(request, pedido_id):
    """Genera y sirve un PDF para un pedido específico."""
    try:
        pedido = Pedido.objects.select_related('cliente').prefetch_related(
            'items__variacion__producto',
            'items__variacion__valores__atributo_def'
        ).get(id=pedido_id)
    except Pedido.DoesNotExist:
        return HttpResponseNotFound("Pedido no encontrado")

    context = {'pedido': pedido}
    pdf = render_to_pdf('catalogo/pedido_pdf.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Pedido_{pedido.id}_{pedido.cliente.nombre.split(' ')[0]}.pdf"
        content = f"attachment; filename=\"{filename}\""
        response['Content-Disposition'] = content
        return response
    
    return HttpResponse("Error al generar el PDF", status=500)


@staff_member_required
@require_http_methods(["GET"])
def valores_por_producto(request):
    """Devuelve los valores de atributo asociados al tipo del producto."""
    producto_id = request.GET.get('producto_id')
    if not producto_id:
        return JsonResponse({'error': 'producto_id requerido'}, status=400)

    try:
        producto = Producto.objects.select_related('categoria__tipo_producto').get(id=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    valores = ValorAtributo.objects.filter(
        atributo_def__tipo_producto=producto.categoria.tipo_producto
    ).values('id', 'valor', 'atributo_def__nombre')

    data = [
        {
            'id': v['id'],
            'label': f"{v['atributo_def__nombre']}: {v['valor']}"
        }
        for v in valores
    ]
    return JsonResponse({'valores': data})
