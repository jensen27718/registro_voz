from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # <-- DESCOMENTA ESTA LÍNEA
    path('', include('interfaz.urls')),
]