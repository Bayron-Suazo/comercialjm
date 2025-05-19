from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

from administraddor.views import listar_mermas
urlpatterns = [
    path('mermas/', listar_mermas, name='listar_mermas'),
    path('', include('core.urls')),
    path('', lambda request: redirect('dashboard/')),  # Redirige raíz a dashboard
    path('dashboard/', include('administraddor.urls')),  # Dashboard de administrador
    path('accounts/', include('django.contrib.auth.urls')),  # Login/logout
]
