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



# ------------------ HOME ------------------



def home(request):
    return redirect('login')



# ------------------ SELECCIONAR ROL ------------------



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
    


@csrf_exempt
@login_required
def seleccionar_rol(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        return redirect_to_dashboard(group_name)
    else:
        return redirect('check_profile')
    


def redirect_to_dashboard(group_name):
    if group_name == 'Administrador':
        return redirect('dashboard_usuarios')
    elif group_name == 'Empleado':
        return redirect('perfil_empleado')
    else:
        return redirect('logout')
from .models import Lote
from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto
from .forms import ProductoForm
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages 


def listar_productos(request):
    from django.template.loader import get_template
    print("🔍 Template usado:", get_template('core/listar_productos.html').origin)

    productos = Producto.objects.filter(activo=True)
    return render(request, 'core/listar_productos.html', {'productos': productos})


from django.contrib import messages

from django.contrib import messages  # Añade esto al inicio si no está

def toggle_estado_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.activo = not producto.activo
    producto.save()

    if producto.activo:
        messages.success(request, "Producto activado con éxito.")
    else:
        messages.warning(request, "Producto desactivado con éxito.")

    origen = request.GET.get('origen', 'activos')
    if origen == 'inactivos':
        return redirect('productos_inactivos')
    return redirect('listar_productos')




def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_productos')
    else:
        form = ProductoForm()
    return render(request, 'core/form_producto.html', {'form': form, 'titulo': 'Agregar Producto'})

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('listar_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'core/form_producto.html', {'form': form, 'titulo': 'Editar Producto'})

def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    return redirect('listar_productos')

def debug_url_test(request):
    try:
        url = reverse('eliminar_producto', kwargs={'id': 1})
        return HttpResponse(f"✅ URL encontrada: {url}")
    except Exception as e:
        return HttpResponse(f"❌ Error: {e}")

def productos_inactivos(request):
    productos = Producto.objects.filter(activo=False)
    return render(request, 'core/productos_inactivos.html', {'productos': productos})

from django.shortcuts import render

def listar_lotes(request):
    lotes = Lote.objects.filter(activo=True)
    return render(request, 'core/listar_lotes.html', {'lotes': lotes})

from django.shortcuts import redirect, get_object_or_404

def bloquear_lote(request, id):
    lote = get_object_or_404(Lote, id=id)
    lote.activo = False
    lote.save()
    return redirect('listar_lotes')
