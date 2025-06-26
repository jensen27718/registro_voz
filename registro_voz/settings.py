import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# settings.py - CÓDIGO UNIFICADO
try:
    # Intenta importar desde el archivo de secretos (esto funcionará en el servidor)
    from . import secrets
except ImportError:
    # Si falla, significa que estamos en local y no hay secrets.py
    secrets = None

# Si 'secrets' fue importado y tiene la clave, úsala.
if hasattr(secrets, 'DJANGO_SECRET_KEY'):
    SECRET_KEY = secrets.DJANGO_SECRET_KEY
else:
    # Si no, usa la variable de entorno de tu archivo local .env
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Para el DEBUG, la lógica se mantiene, leerá de tu .env local.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Configuración para PythonAnywhere y desarrollo local
ALLOWED_HOSTS = [
    'jensenjp08.pythonanywhere.com',  # Reemplaza 'tu-usuario' con tu nombre de usuario de PythonAnywhere
    '127.0.0.1',
    'localhost'
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'interfaz', # Nuestra app
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
        'DIRS': [],
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

# Database
# Usamos la base de datos SQLite por defecto, que no requiere configuración adicional.
# Es suficiente ya que no almacenaremos datos en ella.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    # ... (validadores por defecto)
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# Directorio para archivos estáticos en producción (requerido por PythonAnywhere)
STATIC_ROOT = os.path.join(BASE_DIR, 'static')




# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'