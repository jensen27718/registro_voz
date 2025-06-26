# interfaz/views.py

import os
import json
import gspread
import google.generativeai as genai
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Categoria, Cuenta
from difflib import get_close_matches # Importamos la librería para coincidencias aproximadas
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound
from googleapiclient.discovery import build

# --- CONFIGURACIÓN ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# interfaz/views.py - CÓDIGO UNIFICADO
try:
    # Intenta importar el archivo de secretos del proyecto principal
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
    """
    Busca la hoja de cálculo por su nombre dentro de una carpeta específica.
    Si la hoja o la carpeta no existen, las crea.
    """
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
            print(f"Carpeta '{CONTABILIDAD_FOLDER_NAME}' creada con ID: {folder_id}")

            user_permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': 'artperezjensen@gmail.com'
            }
            drive_service.permissions().create(fileId=folder_id, body=user_permission, fields='id').execute()
            print(f"Carpeta compartida con artperezjensen@gmail.com")

        try:
            spreadsheet = client.open(SHEET_NAME, folder_id=folder_id)
            # print(f"Hoja '{SHEET_NAME}' encontrada.")
            return spreadsheet.sheet1
        except SpreadsheetNotFound:
            print(f"Hoja '{SHEET_NAME}' no encontrada. Creando una nueva...")
            spreadsheet = client.create(SHEET_NAME, folder_id=folder_id)
            worksheet = spreadsheet.sheet1
            worksheet.append_row(HEADERS)
            print(f"Hoja '{SHEET_NAME}' creada y encabezados añadidos.")
            return worksheet
    except Exception as e:
        print(f"Un error ocurrió en get_or_create_worksheet: {e}")
        # En lugar de crashear, devolvemos None para que la vista principal pueda manejar el error.
        return None


def home(request):
    """Renderiza la página principal."""
    return render(request, 'interfaz/voz.html')


@csrf_exempt
def analizar_texto(request):
    """
    Analiza el texto en un solo paso y devuelve las mejores coincidencias
    junto con las listas completas de opciones para el formulario.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        texto_usuario = data.get('texto')

        prompt = f"""
        Extrae los campos {", ".join(HEADERS)} del texto del usuario.
        Extrae la categoría y la cuenta textualmente como las dice el usuario. No intentes validarlas.
        Usa la fecha de hoy ({datetime.now().strftime('%Y-%m-%d')}) si no se especifica.
        Texto del Usuario: "{texto_usuario}"
        
        Responde ÚNICAMENTE con un objeto JSON que tenga una única clave raíz llamada "datos_extraidos".
        EJEMPLO DE RESPUESTA CORRECTA:
        {{
            "datos_extraidos": {{
                "fecha": "2025-06-25",
                "categoria": "Comida",
                "cuenta": "Efectivo",
                "descripcion": "almuerzo en el restaurante",
                "egresos": 150.50,
                "ingresos": 0
            }}
        }}
        """
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('`', '').replace('json', '')
        ai_response = json.loads(cleaned_response)

        # Manejo robusto de la respuesta de la IA (si devuelve lista o dict)
        datos_extraidos = {}
        if isinstance(ai_response, list) and len(ai_response) > 0:
            datos_extraidos = ai_response[0]
        elif isinstance(ai_response, dict):
            datos_extraidos = ai_response.get("datos_extraidos", {})
        
        if not datos_extraidos:
             raise ValueError("La respuesta de la IA no contiene datos extraíbles.")
        
        # --- Lógica de mejor coincidencia en Python (Case-Insensitive) ---
        categorias_db = {c.lower(): c for c in Categoria.objects.values_list('nombre', flat=True)}
        cuentas_db = {c.lower(): c for c in Cuenta.objects.values_list('nombre', flat=True)}

        categoria_usuario_lower = str(datos_extraidos.get('categoria', '')).lower().strip()
        if categoria_usuario_lower:
            sugerencias_cat = get_close_matches(categoria_usuario_lower, list(categorias_db.keys()), n=1, cutoff=0.6)
            datos_extraidos['categoria'] = categorias_db[sugerencias_cat[0]] if sugerencias_cat else ""
        
        cuenta_usuario_lower = str(datos_extraidos.get('cuenta', '')).lower().strip()
        if cuenta_usuario_lower:
            sugerencias_cue = get_close_matches(cuenta_usuario_lower, list(cuentas_db.keys()), n=1, cutoff=0.6)
            datos_extraidos['cuenta'] = cuentas_db[sugerencias_cue[0]] if sugerencias_cue else ""
        
        return JsonResponse({
            'datos_extraidos': datos_extraidos,
            'todas_las_categorias': sorted(list(categorias_db.values())),
            'todas_las_cuentas': sorted(list(cuentas_db.values())),
        })

    except Exception as e:
        print(f"Error en analizar_texto: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def crear_categoria(request):
    """Crea una nueva categoría y devuelve la lista actualizada."""
    if request.method == 'POST':
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        if nombre:
            obj, created = Categoria.objects.get_or_create(nombre=nombre)
            if created: print(f"Nueva categoría creada: {obj.nombre}")
            categorias_actualizadas = sorted(list(Categoria.objects.values_list('nombre', flat=True)))
            return JsonResponse({'status': 'success', 'nuevas_opciones': categorias_actualizadas, 'nuevo_valor': obj.nombre})
    return JsonResponse({'status': 'error', 'message': 'Método no permitido o nombre inválido'}, status=400)

@csrf_exempt
def crear_cuenta(request):
    """Crea una nueva cuenta y devuelve la lista actualizada."""
    if request.method == 'POST':
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        if nombre:
            obj, created = Cuenta.objects.get_or_create(nombre=nombre)
            if created: print(f"Nueva cuenta creada: {obj.nombre}")
            cuentas_actualizadas = sorted(list(Cuenta.objects.values_list('nombre', flat=True)))
            return JsonResponse({'status': 'success', 'nuevas_opciones': cuentas_actualizadas, 'nuevo_valor': obj.nombre})
    return JsonResponse({'status': 'error', 'message': 'Método no permitido o nombre inválido'}, status=400)

@csrf_exempt
def registrar_datos(request):
    """Recibe los datos finales y validados del formulario y los guarda en Google Sheets."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
        datos_finales = data.get('datos')
        if not datos_finales:
            return JsonResponse({'error': 'No se recibieron datos para registrar'}, status=400)
        
        worksheet = get_or_create_worksheet()
        if worksheet is None:
            return JsonResponse({'error': 'No se pudo acceder a la hoja de cálculo.'}, status=500)
        
        fila_a_guardar = [datos_finales.get(h, "") for h in HEADERS]
        worksheet.append_row(fila_a_guardar)
        
        return JsonResponse({'status': 'success', 'message': '¡Registro guardado con éxito!'})
    except Exception as e:
        print(f"Error en registrar_datos: {e}")
        return JsonResponse({'error': str(e)}, status=500)