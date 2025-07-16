# catalogo/views.py

import json
import csv
import io

import cloudinary.uploader

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Prefetch

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
    VariacionBaseForm,
    AtributoDefForm,
    ValorAtributoForm,

    CargaImagenForm,

)
from .models import (
    Cliente, Administrador, TipoProducto, Categoria, Producto,
    AtributoDef, ValorAtributo, VariacionProducto, VariacionBase, Promo,
    Carrito, CarritoItem,
    Pedido, PedidoItem, EstadoPedido
)

WHATSAPP_NUMBER = '573212165252'




def _datos_desde_url(url: str):
    """
    Parsea la información del producto desde el nombre del archivo.
    Formato esperado: "Referencia - Nombre Producto - Categoria1 - Categoria2.jpg"
    """
    fname = url.split('/')[-1]
    try:
        fname_base = fname[:fname.rindex('.')]
    except ValueError:
        fname_base = fname

    parts = [p.strip() for p in fname_base.split('-')]
    
    # Debe haber al menos 3 partes: referencia, nombre, y al menos una categoría.
    if len(parts) < 3:
        print(f"Skipping file with invalid name format: {fname}")
        return None
    
    referencia = parts[0]
    nombre = parts[1]
    # Todas las partes restantes son nombres de categorías.
    cat_nombres = parts[2:]

    return referencia, nombre, cat_nombres



def procesar_imagenes_productos(files, tipo: TipoProducto, heredar: bool):
    """Sube imágenes a Cloudinary y crea/actualiza productos y categorías."""
    for f in files:
        parsed = _datos_desde_url(f.name)
        if not parsed:
            continue
        referencia, nombre, cat_nombres = parsed
        
        try:
            result = cloudinary.uploader.upload(f)
            url = result.get('secure_url') or result.get('url')
        except Exception as e:
            print(f"Error al subir {f.name} a Cloudinary: {e}")
            continue
        
        with transaction.atomic():
            # Obtener o crear todas las categorías necesarias
            categorias_obj = []
            for cat_nombre in cat_nombres:
                categoria, _ = Categoria.objects.get_or_create(
                    tipo_producto=tipo,
                    nombre=cat_nombre,
                    defaults={'imagen_url': url},
                )
                categorias_obj.append(categoria)

            # Crear o actualizar el producto
            producto, created = Producto.objects.update_or_create(
                referencia=referencia,
                defaults={'nombre': nombre, 'foto_url': url}
            )
            
            # Asignar las múltiples categorías al producto
            if categorias_obj:
                producto.categorias.set(categorias_obj)
            
            # Aplicar variaciones base si el producto es nuevo
            if heredar and created:
                for base in VariacionBase.objects.filter(tipo_producto=tipo):
                    var = VariacionProducto.objects.create(
                        producto=producto,
                        precio_base=base.precio_base,
                    )
                    var.valores.set(base.valores.all())


def build_catalog_data():
    """Construye el diccionario de datos inicial para el frontend."""
    productos_qs = Producto.objects.prefetch_related('categorias').all()
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
                # --- LÍNEAS MODIFICADAS ---
                # Ya no existe 'categoriaId'. En su lugar, enviamos una lista de IDs.
                # Renombramos a 'categoriaIds' (plural) para que sea claro en el frontend.
                'categoriaIds': list(p.categorias.values_list('id', flat=True)),
                'nombre': p.nombre,
                'referencia': p.referencia,
                'foto_url': p.foto_url,
            }
            for p in productos_qs  # Usamos la consulta optimizada
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
    edit_base = request.GET.get('edit_base')
    var_prod = request.GET.get('var_prod')

    tipo_form = TipoProductoForm(prefix='tipo', instance=TipoProducto.objects.get(id=edit_tipo) if edit_tipo else None)
    categoria_form = CategoriaForm(prefix='cat', instance=Categoria.objects.get(id=edit_cat) if edit_cat else None)
    producto_form = ProductoForm(prefix='prod', instance=Producto.objects.get(id=edit_prod) if edit_prod else None)
    if edit_var:
        var_instance = VariacionProducto.objects.get(id=edit_var)
        variacion_form = VariacionProductoForm(prefix='var', instance=var_instance)
        var_prod = var_instance.producto_id
    else:
        initial = {'producto': var_prod} if var_prod else None
        variacion_form = VariacionProductoForm(prefix='var', initial=initial)
    base_form = VariacionBaseForm(prefix='base', instance=VariacionBase.objects.get(id=edit_base) if edit_base else None)
    atributo_form = AtributoDefForm(prefix='atr', instance=AtributoDef.objects.get(id=edit_atr) if edit_atr else None)
    valor_form = ValorAtributoForm(prefix='val', instance=ValorAtributo.objects.get(id=edit_val) if edit_val else None)
    

    carga_img_form = CargaImagenForm(prefix='img')


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
        if 'delete_base' in request.POST:
            VariacionBase.objects.filter(id=request.POST['delete_base']).delete()
            return redirect(f"{reverse('catalogo:admin_dashboard')}?section=base")

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
        if 'base-precio_base' in request.POST:
            instance = VariacionBase.objects.get(id=edit_base) if edit_base else None
            base_form = VariacionBaseForm(request.POST, prefix='base', instance=instance)
            if base_form.is_valid():
                base_form.save()
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=base")


        if 'img-imagenes' in request.FILES:
            carga_img_form = CargaImagenForm(request.POST, request.FILES, prefix='img')
            if carga_img_form.is_valid():
                procesar_imagenes_productos(
                    request.FILES.getlist('img-imagenes'),
                    carga_img_form.cleaned_data['tipo_producto'],
                    carga_img_form.cleaned_data['heredar_variaciones'],
                )
                return redirect(f"{reverse('catalogo:admin_dashboard')}?section=carga")


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
    productos = Producto.objects.prefetch_related('categorias').order_by('nombre')

    productos_con_vars_qs = productos.filter(variaciones__isnull=False).distinct().prefetch_related(
        'categorias',
        Prefetch(
            'variaciones',
            queryset=VariacionProducto.objects.prefetch_related('valores__atributo_def'),
        )
    )
    productos_sin_vars_qs = productos.filter(variaciones__isnull=True)

    page_con = request.GET.get('page_con', 1)
    page_sin = request.GET.get('page_sin', 1)
    paginator_con = Paginator(productos_con_vars_qs, 10)
    paginator_sin = Paginator(productos_sin_vars_qs, 10)
    productos_con_vars = paginator_con.get_page(page_con)
    productos_sin_vars = paginator_sin.get_page(page_sin)

    variaciones_base = (
        VariacionBase.objects.select_related('tipo_producto')
        .prefetch_related('valores__atributo_def')
        .order_by('tipo_producto__nombre')
    )

    if var_prod:
        producto_sel = productos.filter(id=var_prod).first()
    else:

        producto_sel = None

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
        'base_form': base_form,
        'carga_img_form': carga_img_form,

        'clientes': clientes,
        'tipos': tipos,
        'categorias': categorias,
        'productos': productos,
        'productos_con_vars': productos_con_vars,
        'productos_sin_vars': productos_sin_vars,
        'producto_sel': producto_sel,
        'variaciones_base': variaciones_base,


        'atributos': atributos,
        'valores': valores,

        'estados': EstadoPedido.choices,
        'section': section,
        'var_prod': var_prod,
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
            'valor': v['valor'],
            'grupo': v['atributo_def__nombre'],
        }
        for v in valores
    ]
    return JsonResponse({'valores': data})


@staff_member_required

@require_http_methods(["GET"])
def valores_por_tipo(request):
    """Devuelve los valores de atributo asociados a un tipo de producto."""
    tipo_id = request.GET.get('tipo_id')
    if not tipo_id:
        return JsonResponse({'error': 'tipo_id requerido'}, status=400)

    try:
        tipo = TipoProducto.objects.get(id=tipo_id)
    except TipoProducto.DoesNotExist:
        return JsonResponse({'error': 'Tipo no encontrado'}, status=404)

    valores = ValorAtributo.objects.filter(
        atributo_def__tipo_producto=tipo
    ).values('id', 'valor', 'atributo_def__nombre')

    data = [
        {
            'id': v['id'],
            'valor': v['valor'],
            'grupo': v['atributo_def__nombre'],
        }
        for v in valores
    ]
    return JsonResponse({'valores': data})


@staff_member_required

@require_http_methods(["POST"])
def aplicar_variaciones_base(request, producto_id):
    next_param = request.POST.get('next')
    if next_param:
        base_url = reverse('catalogo:admin_dashboard')
        next_url = base_url + next_param if next_param.startswith('?') else next_param
    else:
        next_url = reverse('catalogo:admin_dashboard')
    try:
        producto = Producto.objects.select_related('categoria__tipo_producto').get(id=producto_id)
    except Producto.DoesNotExist:
        return HttpResponseNotFound('Producto no encontrado')

    bases = VariacionBase.objects.filter(
        tipo_producto=producto.categoria.tipo_producto
    ).prefetch_related('valores')

    for base in bases:
        exists = False
        for var in producto.variaciones.all():
            if var.precio_base == base.precio_base and set(var.valores.values_list('id', flat=True)) == set(base.valores.values_list('id', flat=True)):
                exists = True
                break
        if not exists:
            variacion = VariacionProducto.objects.create(
                producto=producto,
                precio_base=base.precio_base,
            )
            variacion.valores.set(base.valores.all())

    return redirect(next_url)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_productos(request):
    """Lista de productos o creación de uno nuevo."""
    if request.method == "GET":
        productos = (
            Producto.objects.select_related("categoria")
            .order_by("categoria__nombre", "referencia")
        )
        data = [
            {
                "id": p.id,
                # Devolvemos una lista de IDs y nombres de categorías
                "categoriaIds": list(p.categorias.values_list('id', flat=True)),
                "categorias": list(p.categorias.values_list('nombre', flat=True)),
                "referencia": p.referencia,
                "nombre": p.nombre,
                "foto_url": p.foto_url,
            }
            for p in productos
        ]
        return JsonResponse({"productos": data})

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")

    categoria_id = payload.get("categoriaId")
    referencia = payload.get("referencia", "").strip()
    nombre = payload.get("nombre", "").strip()
    foto_url = payload.get("foto_url", "").strip()

    if not categoria_id or not referencia:
        return HttpResponseBadRequest("categoriaId y referencia requeridos")

    try:
        categoria = Categoria.objects.get(id=categoria_id)
    except Categoria.DoesNotExist:
        return HttpResponseBadRequest("categoria no encontrada")

    producto = Producto.objects.create(
        categoria=categoria,
        referencia=referencia,
        nombre=nombre,
        foto_url=foto_url,
    )

    return JsonResponse(
        {
            "id": producto.id,
            "categoriaId": producto.categoria_id,
            "categoria": categoria.nombre,
            "referencia": producto.referencia,
            "nombre": producto.nombre,
            "foto_url": producto.foto_url,
        },
        status=201,
    )


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def api_producto_detail(request, producto_id):
    """Obtiene, actualiza o elimina un producto específico."""
    try:
        producto = Producto.objects.select_related("categoria").get(id=producto_id)
    except Producto.DoesNotExist:
        return HttpResponseNotFound("producto no encontrado")

    if request.method == "GET":
        return JsonResponse(
            {
                "id": producto.id,
                "categoriaIds": list(producto.categorias.values_list('id', flat=True)),
                "categorias": list(producto.categorias.values_list('nombre', flat=True)),
                "referencia": producto.referencia,
                "nombre": producto.nombre,
                "foto_url": producto.foto_url,
            }
        )

    if request.method == "DELETE":
        producto.delete()
        return JsonResponse({"status": "deleted"})

    # PUT
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")

    if "categoriaId" in payload:
        try:
            categoria = Categoria.objects.get(id=payload["categoriaId"])
            producto.categoria = categoria
        except Categoria.DoesNotExist:
            return HttpResponseBadRequest("categoria no encontrada")

    if "referencia" in payload:
        producto.referencia = payload["referencia"].strip()
    if "nombre" in payload:
        producto.nombre = payload["nombre"].strip()
    if "foto_url" in payload:
        producto.foto_url = payload["foto_url"].strip()
    producto.save()

    return JsonResponse(
        {
            "id": producto.id,
            "categoriaId": producto.categoria_id,
            "categoria": producto.categoria.nombre,
            "referencia": producto.referencia,
            "nombre": producto.nombre,
            "foto_url": producto.foto_url,
        }
    )
