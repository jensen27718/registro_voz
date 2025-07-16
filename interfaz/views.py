import os
import json
import gspread
import google.generativeai as genai
from datetime import datetime, timedelta
from difflib import get_close_matches

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum

from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound
from googleapiclient.discovery import build

from .models import Categoria, Cuenta, Cliente, Registro

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

try:
    from registro_voz import secrets
except ImportError:
    secrets = None

if hasattr(secrets, 'GEMINI_API_KEY'):
    GEMINI_API_KEY = secrets.GEMINI_API_KEY
else:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

CREDS_FILE = os.path.join(settings.BASE_DIR, 'credentials.json')
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
CONTABILIDAD_FOLDER_NAME = "Contabilidad App (Compartida)"
SHEET_NAME = "Registros Contables"
HEADERS = ["fecha", "categoria", "cuenta", "descripcion", "egresos", "ingresos"]


def get_or_create_worksheet():
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        folders_response = drive_service.files().list(
            q=f'mimeType="application/vnd.google-apps.folder" and name="{CONTABILIDAD_FOLDER_NAME}" and trashed=false',
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        folders = folders_response.get('files', [])

        if folders:
            folder_id = folders[0]['id']
        else:
            folder_metadata = {
                'name': CONTABILIDAD_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            user_permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': 'artperezjensen@gmail.com'
            }
            drive_service.permissions().create(fileId=folder_id, body=user_permission, fields='id').execute()

        try:
            spreadsheet = client.open(SHEET_NAME, folder_id=folder_id)
            return spreadsheet.sheet1
        except SpreadsheetNotFound:
            spreadsheet = client.create(SHEET_NAME, folder_id=folder_id)
            worksheet = spreadsheet.sheet1
            worksheet.append_row(HEADERS)
            return worksheet
    except Exception:
        return None


def home(request):
    return render(request, 'interfaz/voz.html')


@csrf_exempt
def analizar_texto(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        texto_usuario = data.get('texto')

        prompt = f"""
        Extrae los campos {', '.join(HEADERS)} y un campo opcional llamado cliente del texto del usuario.
        Extrae la categoría y la cuenta textualmente como las dice el usuario.
        Usa la fecha de hoy ({datetime.now().strftime('%Y-%m-%d')}) si no se especifica.
        Texto del Usuario: "{texto_usuario}"

        Responde ÚNICAMENTE con un objeto JSON llamado "datos_extraidos".
        EJEMPLO:
        {{
            "datos_extraidos": {{
                "fecha": "2025-06-25",
                "categoria": "Comida",
                "cuenta": "Efectivo",
                "descripcion": "almuerzo",
                "egresos": 150.50,
                "ingresos": 0,
                "cliente": "Juan"
            }}
        }}
        """
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace('`', '').replace('json', '')
        ai_response = json.loads(cleaned)
        datos_extraidos = {}
        if isinstance(ai_response, list) and ai_response:
            datos_extraidos = ai_response[0]
        elif isinstance(ai_response, dict):
            datos_extraidos = ai_response.get('datos_extraidos', {})

        categorias_db = {c.lower(): c for c in Categoria.objects.values_list('nombre', flat=True)}
        cuentas_db = {c.lower(): c for c in Cuenta.objects.values_list('nombre', flat=True)}

        cat_lower = str(datos_extraidos.get('categoria', '')).lower().strip()
        if cat_lower:
            match = get_close_matches(cat_lower, list(categorias_db.keys()), n=1, cutoff=0.6)
            datos_extraidos['categoria'] = categorias_db[match[0]] if match else ''

        cue_lower = str(datos_extraidos.get('cuenta', '')).lower().strip()
        if cue_lower:
            match = get_close_matches(cue_lower, list(cuentas_db.keys()), n=1, cutoff=0.6)
            datos_extraidos['cuenta'] = cuentas_db[match[0]] if match else ''

        return JsonResponse({
            'datos_extraidos': datos_extraidos,
            'todas_las_categorias': sorted(list(categorias_db.values())),
            'todas_las_cuentas': sorted(list(cuentas_db.values())),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def crear_categoria(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        if nombre:
            obj, _ = Categoria.objects.get_or_create(nombre=nombre)
            categorias_actualizadas = sorted(list(Categoria.objects.values_list('nombre', flat=True)))
            return JsonResponse({'status': 'success', 'nuevas_opciones': categorias_actualizadas, 'nuevo_valor': obj.nombre})
    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def crear_cuenta(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        if nombre:
            obj, _ = Cuenta.objects.get_or_create(nombre=nombre)
            cuentas_actualizadas = sorted(list(Cuenta.objects.values_list('nombre', flat=True)))
            return JsonResponse({'status': 'success', 'nuevas_opciones': cuentas_actualizadas, 'nuevo_valor': obj.nombre})
    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def registrar_datos(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
        datos_finales = data.get('datos')
        if not datos_finales:
            return JsonResponse({'error': 'No se recibieron datos'}, status=400)

        worksheet = get_or_create_worksheet()
        if worksheet is None:
            return JsonResponse({'error': 'No se pudo acceder a la hoja de cálculo.'}, status=500)

        fila = [datos_finales.get(h, '') for h in HEADERS]
        worksheet.append_row(fila)

        cliente_obj = None
        nombre_cliente = datos_finales.get('cliente')
        if nombre_cliente:
            cliente_obj, _ = Cliente.objects.get_or_create(nombre=nombre_cliente)

        Registro.objects.create(
            fecha=datos_finales.get('fecha') or timezone.now().date(),
            descripcion=datos_finales.get('descripcion', ''),
            categoria=Categoria.objects.filter(nombre=datos_finales.get('categoria')).first(),
            cuenta=Cuenta.objects.filter(nombre=datos_finales.get('cuenta')).first(),
            egresos=datos_finales.get('egresos') or 0,
            ingresos=datos_finales.get('ingresos') or 0,
            cliente=cliente_obj
        )

        return JsonResponse({'status': 'success', 'message': '¡Registro guardado con éxito!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def _totales_desde(qs):
    ingresos = qs.aggregate(total=Sum('ingresos'))['total'] or 0
    egresos = qs.aggregate(total=Sum('egresos'))['total'] or 0
    return {
        'ingresos': ingresos,
        'egresos': egresos,
        'saldo': ingresos - egresos,
    }


def dashboard(request):
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    inicio_anio = hoy.replace(month=1, day=1)


    totales_semana = _totales_desde(
        Registro.objects.filter(
            fecha__range=[inicio_semana, inicio_semana + timedelta(days=6)]
        )
    )

    totales_mes = _totales_desde(Registro.objects.filter(fecha__gte=inicio_mes))
    totales_anio = _totales_desde(Registro.objects.filter(fecha__gte=inicio_anio))
    recientes = Registro.objects.order_by('-fecha', '-id')[:10]


    cuentas_data = []
    for cuenta in Cuenta.objects.all():
        qs_cuenta = Registro.objects.filter(cuenta=cuenta)
        cuentas_data.append(
            {
                'cuenta': cuenta,
                'saldo_actual': _totales_desde(qs_cuenta)['saldo'],
                'totales_semana': _totales_desde(
                    qs_cuenta.filter(
                        fecha__range=[inicio_semana, inicio_semana + timedelta(days=6)]
                    )
                ),
                'totales_mes': _totales_desde(qs_cuenta.filter(fecha__gte=inicio_mes)),
                'totales_anio': _totales_desde(qs_cuenta.filter(fecha__gte=inicio_anio)),
            }
        )

    context = {
        'totales_semana': totales_semana,
        'totales_mes': totales_mes,
        'totales_anio': totales_anio,
        'registros_recientes': recientes,

        'cuentas_data': cuentas_data,

    }
    return render(request, 'interfaz/dashboard.html', context)


def editar_registro(request, registro_id):
    registro = get_object_or_404(Registro, id=registro_id)
    if request.method == 'POST':
        registro.fecha = request.POST.get('fecha', registro.fecha)
        registro.descripcion = request.POST.get('descripcion', '')
        registro.egresos = request.POST.get('egresos') or 0
        registro.ingresos = request.POST.get('ingresos') or 0
        registro.categoria = Categoria.objects.filter(nombre=request.POST.get('categoria')).first()
        registro.cuenta = Cuenta.objects.filter(nombre=request.POST.get('cuenta')).first()
        nombre_cliente = request.POST.get('cliente')
        if nombre_cliente:
            registro.cliente, _ = Cliente.objects.get_or_create(nombre=nombre_cliente)
        else:
            registro.cliente = None
        registro.save()
        return redirect('interfaz:dashboard')

    context = {
        'registro': registro,
        'categorias': Categoria.objects.all(),
        'cuentas': Cuenta.objects.all(),
    }
    return render(request, 'interfaz/editar_registro.html', context)


@csrf_exempt
def eliminar_registro(request, registro_id):
    registro = get_object_or_404(Registro, id=registro_id)
    if request.method == 'POST':
        registro.delete()
        return redirect('interfaz:dashboard')
    return JsonResponse({'error': 'Método no permitido'}, status=405)
