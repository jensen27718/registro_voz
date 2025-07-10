# registro_voz/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    # La app original de contabilidad puede omitirse en entornos sin credenciales
    *([] if os.environ.get('NO_INTERFAZ') else [path('contabilidad/', include('interfaz.urls'))]),

    # <-- NUEVAS RUTAS PARA EL GESTOR DE TAREAS -->
    path('tareas/', include('gestor_tareas.urls')),
    path('catalogo/', include('catalogo.urls')),

    # Redirigir la raíz del sitio a la lista de tareas
    path('', RedirectView.as_view(url='/catalogo/', permanent=True)),
]