# gestor_tareas/views.py

import os
import json
import tempfile
import google.generativeai as genai
from datetime import datetime
from difflib import get_close_matches

import cloudinary.uploader
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q

from .models import Tarea, TipoTrabajo, DetalleTarea
from catalogo.models import (
    TipoProducto as CatalogoTipoProducto,
    VariacionProducto,
    ValorAtributo,
)
from .ocr.gemini_ocr_processor import GeminiOCRProcessor

# --- CONFIGURACIÓN DE IA ---
# Intenta cargar la clave API desde un archivo 'secrets.py' (para producción)
# o desde variables de entorno (para desarrollo local).
try:
    from registro_voz import secrets
    GEMINI_API_KEY = secrets.GEMINI_API_KEY
except (ImportError, AttributeError):
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Configura la biblioteca de Gemini si se encontró una clave.
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# --- VISTAS PRINCIPALES DE LA APLICACIÓN ---

def listar_tareas(request):
    """Listado principal de tareas con búsqueda, filtros y orden."""
    tareas_visibles = Tarea.objects.filter(is_visible=True).select_related('tipo')

    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    prioridad = request.GET.get('prioridad', '')
    tipo = request.GET.get('tipo', '')

    if q:
        tareas_visibles = tareas_visibles.filter(
            Q(cliente__icontains=q) |
            Q(telefono__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(tipo__nombre__icontains=q)
        )
    if estado:
        tareas_visibles = tareas_visibles.filter(estado=estado)
    if prioridad:
        tareas_visibles = tareas_visibles.filter(prioridad=prioridad)
    if tipo:
        tareas_visibles = tareas_visibles.filter(tipo__nombre=tipo)

    prioridades_posibles = (
        Tarea.objects.values_list('prioridad', flat=True).distinct()
    )
    tipos_posibles = TipoTrabajo.objects.values_list('nombre', flat=True)

    context = {
        'tareas': tareas_visibles,
        'estados_posibles': Tarea.Estado.choices,
        'prioridades_posibles': prioridades_posibles,
        'tipos_posibles': tipos_posibles,
        'filtros': {
            'q': q,
            'estado': estado,
            'prioridad': prioridad,
            'tipo': tipo,
        }
    }
    return render(request, 'gestor_tareas/lista_tareas.html', context)

def agregar_tarea_voz(request):
    """
    Renderiza la página que contiene el micrófono para agregar una nueva tarea por voz.
    """
    return render(
        request,
        'gestor_tareas/agregar_tarea.html',
        {
            'tipos': list(TipoTrabajo.objects.values_list('nombre', flat=True)),
            'prioridades': [p[0] for p in Tarea.Prioridad.choices],
            'estados': [e[0] for e in Tarea.Estado.choices],
        },
    )

def editar_tarea(request, tarea_id):
    """
    Maneja la edición de una tarea existente.
    - Si es GET, muestra el formulario con los datos actuales de la tarea.
    - Si es POST, procesa los datos enviados y guarda los cambios.
    """
    tarea = get_object_or_404(Tarea, id=tarea_id)

    if request.method == 'POST':
        # Procesa el formulario enviado
        tarea.cliente = request.POST.get('cliente', '')
        tarea.telefono = request.POST.get('telefono', '')
        tarea.prioridad = request.POST.get('prioridad', Tarea.Prioridad.NORMAL)
        tarea.estado = request.POST.get('estado', Tarea.Estado.RECIBIDO)
        tarea.descripcion = request.POST.get('descripcion', '')
        tarea.orden = request.POST.get('orden') or None
        
        # Maneja la relación con TipoTrabajo
        tipo_nombre = request.POST.get('tipo')
        tarea.tipo = TipoTrabajo.objects.filter(nombre=tipo_nombre).first()
        
        tarea.save()  # Guarda los cambios en la base de datos

        # Actualiza el estado de los detalles (checklist)
        for detalle in tarea.detalles.all():
            key = f"detalle-{detalle.id}-completado"
            detalle.completado = key in request.POST
            detalle.save(update_fields=['completado'])

        return redirect('gestor_tareas:lista_tareas')  # Redirige a la lista

    # Si es una petición GET, muestra el formulario de edición
    context = {
        'tarea': tarea,
        'todos_los_tipos': TipoTrabajo.objects.all(),
        'todas_las_prioridades': Tarea.Prioridad.choices,
        'todos_los_estados': Tarea.Estado.choices,
        'detalles': tarea.detalles.select_related('variacion', 'tipo_producto').all(),
        'tipos_producto_catalogo': CatalogoTipoProducto.objects.all(),
        'variaciones_catalogo': VariacionProducto.objects.select_related('producto').all(),
        'tamanos': ValorAtributo.objects.filter(atributo_def__nombre__iexact='Tamaño'),
        'colores': ValorAtributo.objects.filter(atributo_def__nombre__iexact='Color'),
    }
    return render(request, 'gestor_tareas/editar_tarea.html', context)


@csrf_exempt
def agregar_detalle(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    if request.method == 'POST':
        tipo_id = request.POST.get('tipo_producto')
        variacion_id = request.POST.get('variacion') or None
        descripcion = request.POST.get('descripcion', '')
        datos = request.POST.get('datos_adicionales', '')
        cantidad = int(request.POST.get('cantidad', '1') or '1')
        tamano_id = request.POST.get('tamano') or None
        color_id = request.POST.get('color') or None

        imagen_url = ''
        if request.FILES.get('imagen'):
            try:
                result = cloudinary.uploader.upload(request.FILES['imagen'])
                imagen_url = result.get('secure_url') or result.get('url')
            except Exception:
                imagen_url = ''

        tipo_producto = CatalogoTipoProducto.objects.filter(id=tipo_id).first()
        variacion = VariacionProducto.objects.filter(id=variacion_id).first() if variacion_id else None
        tamano = ValorAtributo.objects.filter(id=tamano_id).first() if tamano_id else None
        color = ValorAtributo.objects.filter(id=color_id).first() if color_id else None

        DetalleTarea.objects.create(
            tarea=tarea,
            tipo_producto=tipo_producto,
            variacion=variacion,
            descripcion=descripcion,
            datos_adicionales=datos,
            cantidad=cantidad,
            tamano=tamano,
            color=color,
            imagen_url=imagen_url,
        )

    return redirect('gestor_tareas:editar_tarea', tarea_id=tarea.id)


class _SimpleConfig:
    def get_colors(self):
        return list(
            ValorAtributo.objects.filter(atributo_def__nombre__iexact='Color')
            .values_list('valor', flat=True)
        )


@csrf_exempt
def ocr_detalles(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    if request.method == 'POST' and request.FILES.get('imagen'):
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                for chunk in request.FILES['imagen'].chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            processor = GeminiOCRProcessor(GEMINI_API_KEY, _SimpleConfig())
            registros, error = processor.process_image_to_extract_data(tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        if error:
            return JsonResponse({'error': error}, status=400)
        for item in registros:
            ref = item.get('ref')
            qty = int(item.get('qty', 1))
            tam_nombre = item.get('tamaño')
            color_nombre = item.get('color')
            tam = ValorAtributo.objects.filter(valor__iexact=tam_nombre).first()
            color = ValorAtributo.objects.filter(valor__iexact=color_nombre).first()
            variacion = None
            tipo_producto = None
            if ref:
                variacion = (
                    VariacionProducto.objects.filter(
                        producto__referencia__iexact=ref,
                        valores=tam,
                    )
                    .filter(valores=color)
                    .first()
                )
                if variacion:
                    cat = variacion.producto.categorias.first()
                    if cat:
                        tipo_producto = cat.tipo_producto
            DetalleTarea.objects.create(
                tarea=tarea,
                tipo_producto=tipo_producto,
                variacion=variacion,
                referencia=ref,
                cantidad=qty,
                tamano=tam,
                color=color,
            )
        return redirect('gestor_tareas:editar_tarea', tarea_id=tarea.id)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# --- VISTAS DE API / BACKEND (Manejan peticiones AJAX) ---

@csrf_exempt
def analizar_texto_tarea(request):
    """
    Recibe un texto del frontend, lo envía a la IA de Gemini para su análisis
    y devuelve los datos extraídos en formato JSON para rellenar el formulario.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        texto_usuario = data.get('texto')

        # El prompt es la instrucción que se le da a la IA.
        prompt = f"""
        Extrae los campos para una tarea del siguiente texto.
        Los campos son: cliente, tipo, descripcion, telefono, prioridad.
        El estado por defecto es 'Recibido'.
        La fecha de recibido es hoy: {timezone.now().strftime('%Y-%m-%d')}.
        Prioridades válidas: Normal, Urgente.

        Texto del Usuario: "{texto_usuario}"
        
        Responde ÚNICAMENTE con un objeto JSON con la clave "datos_extraidos".
        EJEMPLO DE RESPUESTA:
        {{
            "datos_extraidos": {{
                "cliente": "Carlos Mendoza",
                "tipo": "Globos",
                "descripcion": "un arreglo de globos de cumpleaños para el sábado",
                "telefono": "555-1234",
                "prioridad": "Normal"
            }}
        }}
        """
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Limpia la respuesta de la IA para asegurar que sea un JSON válido.
        cleaned_response = response.text.strip().replace('`', '').replace('json', '')
        ai_response = json.loads(cleaned_response)
        datos_extraidos = ai_response.get("datos_extraidos", {})

        if not datos_extraidos:
            raise ValueError("La IA no pudo extraer datos del texto.")

        # Busca la mejor coincidencia para el 'tipo' de trabajo en la BD.
        tipos_db = {t.lower(): t for t in TipoTrabajo.objects.values_list('nombre', flat=True)}
        tipo_usuario_lower = str(datos_extraidos.get('tipo', '')).lower().strip()
        if tipo_usuario_lower and tipos_db:
            sugerencias = get_close_matches(tipo_usuario_lower, list(tipos_db.keys()), n=1, cutoff=0.6)
            datos_extraidos['tipo'] = tipos_db[sugerencias[0]] if sugerencias else ""

        # Devuelve los datos extraídos y las listas de opciones para los selects.
        return JsonResponse({
            'datos_extraidos': datos_extraidos,
            'todos_los_tipos': sorted(list(tipos_db.values())),
            'todas_las_prioridades': [p[0] for p in Tarea.Prioridad.choices],
            'todos_los_estados': [e[0] for e in Tarea.Estado.choices],
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def registrar_tarea(request):
    """
    Recibe los datos finales del formulario y crea un nuevo registro de Tarea en la BD.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body).get('datos')
        if not data:
            return JsonResponse({'error': 'No se recibieron datos.'}, status=400)

        tipo_obj = TipoTrabajo.objects.filter(nombre=data.get('tipo')).first()

        Tarea.objects.create(
            fecha_recibido=data.get('fecha_recibido') or timezone.now().date(),
            prioridad=data.get('prioridad', Tarea.Prioridad.NORMAL),
            estado=data.get('estado', Tarea.Estado.RECIBIDO),
            cliente=data.get('cliente', 'N/A'),
            tipo=tipo_obj,
            telefono=data.get('telefono', ''),
            descripcion=data.get('descripcion', ''),
            orden=data.get('orden')
        )
        return JsonResponse({'status': 'success', 'message': '¡Tarea registrada con éxito!'})

    except Exception as e:
        return JsonResponse({'error': f'Error al guardar en la base de datos: {e}'}, status=500)

@csrf_exempt
def actualizar_estado_tarea(request):
    """
    Actualiza el estado de una tarea dinámicamente desde la lista principal.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        tarea = Tarea.objects.get(id=data.get('tarea_id'))
        tarea.estado = data.get('nuevo_estado')
        tarea.save()  # El método save() del modelo se encarga de la fecha_completado.

        return JsonResponse({
            'status': 'success',
            'message': f'Tarea #{tarea.id} actualizada a "{tarea.estado}".',
            'fecha_completado': tarea.fecha_completado.strftime('%Y-%m-%d') if tarea.fecha_completado else ''
        })
    except Tarea.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'La tarea no existe.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def reordenar_tareas(request):
    """Actualiza el orden de múltiples tareas."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
        ordenes = data.get('ordenes', [])
        for item in ordenes:
            Tarea.objects.filter(id=item.get('id')).update(orden=item.get('orden'))
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def ocultar_tarea(request, tarea_id):
    """
    Marca una tarea como no visible (la archiva) para que no aparezca en la lista.
    """
    if request.method == 'POST':
        try:
            tarea = Tarea.objects.get(id=tarea_id)
            tarea.is_visible = False
            tarea.save()
            return JsonResponse({'status': 'success', 'message': f'Tarea #{tarea_id} archivada.'})
        except Tarea.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'La tarea no existe.'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@csrf_exempt
def crear_tipo_trabajo(request):
    """
    Permite crear un nuevo 'TipoTrabajo' sobre la marcha desde el formulario.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        if nombre:
            obj, _ = TipoTrabajo.objects.get_or_create(nombre=nombre)
            tipos_actualizados = sorted(list(TipoTrabajo.objects.values_list('nombre', flat=True)))
            return JsonResponse({'status': 'success', 'nuevas_opciones': tipos_actualizados, 'nuevo_valor': obj.nombre})
    return JsonResponse({'status': 'error'}, status=400)