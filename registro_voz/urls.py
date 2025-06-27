# registro_voz/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # La app original de contabilidad (opcional, se puede mantener o quitar)
    path('contabilidad/', include('interfaz.urls')),
    
    # <-- NUEVAS RUTAS PARA EL GESTOR DE TAREAS -->
    path('tareas/', include('gestor_tareas.urls')),

    # Redirigir la raíz del sitio a la lista de tareas
    path('', RedirectView.as_view(url='/tareas/', permanent=True)),
]