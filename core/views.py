from django.shortcuts import render
from django.conf import settings #importa el archivo settings
from django.contrib import messages #habilita la mesajería entre vistas
from django.contrib.auth.decorators import login_required #habilita el decorador que se niega el acceso a una función si no se esta logeado
from django.contrib.auth.models import Group, User # importa los models de usuarios y grupos
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator #permite la paqinación
from django.db.models import Avg, Count, Q #agrega funcionalidades de agregación a nuestros QuerySets
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotFound, HttpResponseRedirect) #Salidas alternativas al flujo de la aplicación se explicará mas adelante
from django.shortcuts import redirect, render #permite renderizar vistas basadas en funciones o redireccionar a otras funciones
from django.template import RequestContext # contexto del sistema
from django.views.decorators.csrf import csrf_exempt #decorador que nos permitira realizar conexiones csrf

from registration.models import Profile #importa el modelo profile, el que usaremos para los perfiles de usuarios

# Create your views here.
def home(request):
    return redirect('login')

@login_required
def check_profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, 'Hubo un error con su usuario, por favor contáctese con los administradores')
        return redirect('login')

    groups = profile.groups.all()

    if groups.count() == 1:
        group_name = groups.first().name
        return redirect_to_dashboard(group_name)

    elif groups.count() > 1:
        return render(request, 'core/seleccionar_rol.html', {'groups': groups})
    else:
        messages.error(request, 'No tiene roles asignados')
        return redirect('logout')

def redirect_to_dashboard(group_name):
    if group_name == 'Administrador':
        return redirect('dashboard_usuarios')
    elif group_name == 'Empleado':
        return redirect('perfil_empleado')
    else:
        return redirect('logout')

@csrf_exempt
@login_required
def seleccionar_rol(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        return redirect_to_dashboard(group_name)
    else:
        return redirect('check_profile')
    
