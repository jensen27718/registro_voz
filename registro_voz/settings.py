# registro_voz/settings.py

import os
from pathlib import Path
import cloudinary
import urllib.parse

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- 2. LÓGICA DE CONFIGURACIÓN DUAL (PRODUCCIÓN vs. LOCAL) ---

# Variable para almacenar la URL de Cloudinary
cloudinary_url = None

# Intentamos importar desde 'secrets.py'. Si tiene éxito, estamos en producción.
try:
    from . import secrets
    
    # --- CONFIGURACIÓN PARA PRODUCCIÓN (PythonAnywhere) ---
    SECRET_KEY = secrets.DJANGO_SECRET_KEY
    DEBUG = False
    
    if hasattr(secrets, 'CLOUDINARY_URL'):
        cloudinary_url = secrets.CLOUDINARY_URL

# Si 'secrets.py' no existe, estamos en desarrollo local.
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    
    # --- CONFIGURACIÓN PARA DESARROLLO LOCAL ---
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
    
    cloudinary_url = os.environ.get('CLOUDINARY_URL')


# --- 3. CONFIGURACIÓN EXPLÍCITA DE CLOUDINARY (UNIFICADA) ---
# Este bloque se ejecuta para ambos entornos, usando la variable `cloudinary_url`
# que se haya obtenido en el paso anterior.

if cloudinary_url:
    try:
        # Descomponemos la URL en sus partes
        parsed_url = urllib.parse.urlparse(cloudinary_url)
        
        # Configuramos la librería explícitamente usando las partes de la URL
        cloudinary.config(
          cloud_name = parsed_url.hostname,
          api_key = parsed_url.username,
          api_secret = parsed_url.password,
          secure = True
        )
        print("INFO: Cloudinary configurado exitosamente.") # Mensaje de confirmación
    except Exception as e:
        print(f"ERROR: Falló la configuración de Cloudinary - {e}")

else:
    print("ADVERTENCIA: CLOUDINARY_URL no encontrada. La subida de imágenes fallará.")


# --- 4. CONFIGURACIÓN DE SEGURIDAD Y APLICACIÓN ---

ALLOWED_HOSTS = ['jensenjp08.pythonanywhere.com']
if DEBUG:
    ALLOWED_HOSTS.extend(['127.0.0.1', 'localhost'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'interfaz',
    'gestor_tareas',
    'catalogo',
    'cloudinary',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'registro_voz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'registro_voz.wsgi.application'


# --- 5. BASE DE DATOS Y OTROS AJUSTES ---

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'