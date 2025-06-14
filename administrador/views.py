from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from .forms import UserProfileForm
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import CargaMasivaUsuariosForm
from registration.models import Profile, Proveedor, Compra, Producto, DetalleCompra, Merma, DetalleLote, Lote, Cliente
from datetime import datetime, date
from django.core.exceptions import ValidationError
from django.contrib import messages
from administrador.forms import EditUserProfileForm, CrearProveedorForm, EditarProveedorForm, CompraForm, DetalleCompraForm, CargaMasivaProveedorForm, CargaMasivaUsuariosForm, AprobarCompraForm
from django.views.decorators.http import require_POST
from .forms import PerfilForm
from django.db.models import Count, Avg, Max, Min
from django.db import transaction
from collections import defaultdict
from django.forms import formset_factory
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Count, Sum, F, Q,  ExpressionWrapper, FloatField
from django.contrib import messages
from .forms import ProductoForm, MermaForm
from registration.models import Profile, Venta
from .forms import ClienteForm
from django.core.exceptions import ObjectDoesNotExist
from openpyxl import load_workbook
import traceback
from django.utils.crypto import get_random_string
from openpyxl.utils.datetime import from_excel
from django.utils.timezone import now, timedelta
import re, random, string, uuid, csv, json
from django.utils.dateparse import parse_date
from django.core.validators import validate_email
from django.template.loader import get_template
from weasyprint import HTML
from io import BytesIO


# ------------------------------------ GESTIÓN DE USUARIOS ------------------------------------



# ------------------ LISTADO DE USUARIOS ACTIVOS Y BLOQUEADOS ------------------



@login_required
def lista_usuarios_activos(request):
    order_by = request.GET.get('order_by', '')

    usuarios_activos = User.objects.filter(is_active=True)

    if order_by:
        if order_by == 'first_name':
            usuarios = usuarios_activos.order_by('first_name')
        elif order_by == 'last_name':
            usuarios = usuarios_activos.order_by('last_name')
        elif order_by == 'rut':
            usuarios = usuarios_activos.order_by('profile__rut')
        else:
            usuarios = usuarios_activos
    else:
        usuarios = usuarios_activos
    
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'administrador/lista_usuarios.html', {'usuarios': usuarios, 'order_by': order_by})



@login_required
def lista_usuarios_bloqueados(request):
    order_by = request.GET.get('order_by', '')

    usuarios_bloqueados = User.objects.filter(is_active=False)

    if order_by:
        if order_by == 'first_name':
            usuarios = usuarios_bloqueados.order_by('first_name')
        elif order_by == 'last_name':
            usuarios = usuarios_bloqueados.order_by('last_name')
        elif order_by == 'rut':
            usuarios = usuarios_bloqueados.order_by('profile__rut')
        elif order_by == 'group':
            usuarios = usuarios_bloqueados.order_by('groups__name')
        else:
            usuarios = usuarios_bloqueados 
    else:
        usuarios = usuarios_bloqueados  

    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'administrador/lista_usuarios_bloqueados.html', {'usuarios': usuarios, 'order_by': order_by})



# ------------------ AGREGAR - MOSTRAR - EDITAR - ACTIVAR - BLOQUEAR ------------------



@login_required
def agregar_usuario(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            profile, password = form.save()
            user = profile.user

            # Enviar correo
            asunto = f"Cuenta creada correctamente en Comercial JM para {user.first_name} {user.last_name}"
            mensaje = f"""
                Hola {user.first_name} {user.last_name},

                Tu cuenta en Comercial JM ha sido creada exitosamente.

                Puedes acceder al sistema en el siguiente enlace:
                http://127.0.0.1:8000/accounts/login/

                Tus credenciales de acceso son:

                Usuario: {user.username}
                Contraseña: {password}

                Por seguridad, te recomendamos cambiar tu contraseña después de iniciar sesión.

                Saludos cordiales,  
                Equipo Comercial JM
            """

            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return redirect('lista_usuarios_activos')
    else:
        form = UserProfileForm()
    return render(request, 'administrador/agregar_usuario.html', {'form': form})



@login_required
def mostrar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'administrador/mostrar_usuario.html', {'user': user})



@login_required
def editar_usuario(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile = get_object_or_404(Profile, user=user)

    if request.method == 'POST':
        form = EditUserProfileForm(request.POST, instance=profile, user_instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = EditUserProfileForm(instance=profile, user_instance=user)
        return render(request, 'administrador/editar_usuario.html', {
            'user_form': form,
            'user': user
        })



@require_POST
@login_required
def activar_usuario(request):
    try:
        user_id = request.POST.get('user_id')
        user_ids = json.loads(request.POST.get('user_ids', '[]')) if request.POST.get('user_ids') else []

        if user_id:
            if int(user_id) == request.user.id:
                return JsonResponse({'success': False})
            user_ids = [user_id]

        user_ids = [int(uid) for uid in user_ids if int(uid) != request.user.id]
        users = User.objects.filter(id__in=user_ids, is_active=False)

        from registration.models import Profile
        updated_count = 0

        for user in users:
            user.is_active = True
            user.save()
            Profile.objects.filter(user=user).update(failed_attempts=0)
            updated_count += 1

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@require_POST
@login_required
def bloquear_usuario(request):
    try:
        user_id = request.POST.get('user_id')
        user_ids = json.loads(request.POST.get('user_ids', '[]')) if request.POST.get('user_ids') else []

        if user_id:
            if int(user_id) == request.user.id:
                return JsonResponse({'success': False})
            user_ids = [user_id]

        user_ids = [int(uid) for uid in user_ids if int(uid) != request.user.id]
        users = User.objects.filter(id__in=user_ids, is_active=True)
        updated_count = users.update(is_active=False)

        return JsonResponse({'success': True, 'updated': updated_count})
    except:
        return JsonResponse({'success': False})
    


# ------------------ ACTUALIZAR CREDENCIALES ------------------



def generar_password_aleatoria(longitud=10):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))

def cambiar_credenciales(request, user_id):
    if request.method == 'POST':
        admin_password = request.POST.get('admin_password')
        confirm_text = request.POST.get('confirm_text')
        usuario_objetivo = get_object_or_404(User, id=user_id)

        if not request.user.is_superuser:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return redirect('mostrar_usuario', user_id)

        user_auth = authenticate(username=request.user.username, password=admin_password)
        if not user_auth:
            messages.error(request, "Contraseña de administrador incorrecta.")
            return redirect('mostrar_usuario', user_id)

        if confirm_text.strip().lower() != "confirmar":
            messages.error(request, "Debe escribir 'confirmar' para continuar.")
            return redirect('mostrar_usuario', user_id)

        # Generar y asignar nueva contraseña
        nueva_password = generar_password_aleatoria()
        usuario_objetivo.set_password(nueva_password)
        usuario_objetivo.save()

        # Enviar correo con nuevas credenciales
        send_mail(
            subject='Actualización de credenciales',
            message=(
                f'Hola usuario {usuario_objetivo.first_name},\n\n'
                f'Le informamos que su contraseña ha sido actualizada recientemente por un administrador.\n'
                f'Su nombre de usuario en caso de que lo haya olvidado es: {usuario_objetivo.username}\n'
                f'Su nueva contraseña es: {nueva_password}\n\n'
                'Por favor, inicie sesión y cámbiela lo antes posible.\n'
                f'Equipo ComercialJM\n'
            ),
            from_email='noreply@tusistema.com',
            recipient_list=[usuario_objetivo.email],
            fail_silently=False
        )

        messages.success(request, "Contraseña actualizada y enviada por correo.")
        return redirect('mostrar_usuario', user_id)
    


# ------------------ VISTA PERFIL ------------------



@login_required
def perfil_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        # Obtener datos del formulario
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()

        # Validar que no haya campos vacíos
        if not all([first_name, last_name, email, telefono, direccion]):
            return render(request, 'administrador/perfil.html', {'user': user})

        # Si pasa validación, actualizar datos
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        profile.telefono = telefono
        profile.direccion = direccion
        profile.save()

        return redirect('perfil_admin')

    return render(request, 'administrador/perfil.html', {'user': user})



# ------------------ CARGA MASIVA ------------------


def carga_masiva_usuarios(request):
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']

        try:
            df = pd.read_excel(archivo)

            campos_requeridos = [
                'rut', 'first_name', 'last_name', 'sexo', 'correo',
                'telefono', 'direccion', 'fecha_nacimiento', 'cargo'
            ]
            for campo in campos_requeridos:
                if campo not in df.columns:
                    messages.error(request, f"Falta la columna: {campo}")
                    return redirect('lista_usuarios_activos')

            usuarios_creados = 0
            usuarios_omitidos = 0

            for index, row in df.iterrows():
                fila = index + 2

                try:
                    rut = str(row['rut']).strip()
                    first_name = str(row['first_name']).strip()
                    last_name = str(row['last_name']).strip()
                    sexo = str(row['sexo']).strip().upper()
                    correo = str(row['correo']).strip()
                    telefono = str(row['telefono']).strip()
                    direccion = str(row['direccion']).strip()
                    cargo = str(row['cargo']).strip()

                    # Validar RUT
                    if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', rut):
                        messages.warning(request, f"Fila {fila}: RUT inválido (formato esperado XX.XXX.XXX-X)")
                        usuarios_omitidos += 1
                        continue

                    # Validar nombres
                    if not re.match(r'^([A-Za-zÁÉÍÓÚáéíóúÑñ]+(\s)?){1,3}$', first_name):
                        messages.warning(request, f"Fila {fila}: Nombre inválido (solo letras, máximo 3 palabras)")
                        usuarios_omitidos += 1
                        continue

                    # Validar apellidos
                    if not re.match(r'^([A-Za-zÁÉÍÓÚáéíóúÑñ]+(\s)?){1,2}$', last_name):
                        messages.warning(request, f"Fila {fila}: Apellido inválido (solo letras, máximo 2 palabras)")
                        usuarios_omitidos += 1
                        continue

                    # Validar sexo
                    if sexo not in ['M', 'F']:
                        messages.warning(request, f"Fila {fila}: Sexo inválido (solo 'M' o 'F')")
                        usuarios_omitidos += 1
                        continue

                    # Validar correo
                    try:
                        validate_email(correo)
                    except ValidationError:
                        messages.warning(request, f"Fila {fila}: Correo inválido")
                        usuarios_omitidos += 1
                        continue

                    # Validar teléfono
                    if not re.match(r'^\d\s\d{4}\s\d{4}$', telefono):
                        messages.warning(request, f"Fila {fila}: Teléfono inválido (formato esperado: 9 1234 5678)")
                        usuarios_omitidos += 1
                        continue

                    # Validar cargo
                    if cargo not in ['Empleado', 'Administrador']:
                        messages.warning(request, f"Fila {fila}: Cargo inválido (solo 'Empleado' o 'Administrador')")
                        usuarios_omitidos += 1
                        continue

                    # Validar existencia
                    if Profile.objects.filter(rut=rut).exists() or User.objects.filter(username=rut).exists():
                        messages.warning(request, f"Fila {fila}: Usuario con ese RUT ya existe")
                        usuarios_omitidos += 1
                        continue

                    # Fecha de nacimiento
                    fecha_raw = row['fecha_nacimiento']
                    if pd.isna(fecha_raw):
                        fecha_nacimiento = None
                    elif isinstance(fecha_raw, str):
                        fecha_nacimiento = parse_date(fecha_raw)
                    else:
                        fecha_nacimiento = pd.to_datetime(fecha_raw).date()

                    # Crear usuario
                    password = get_random_string(12)
                    user = User(
                        username=rut,
                        first_name=first_name,
                        last_name=last_name,
                        email=correo
                    )
                    user.set_password(password)
                    user.save()

                    # Crear perfil
                    profile = Profile.objects.create(
                        user=user,
                        rut=rut,
                        telefono=telefono,
                        fecha_nacimiento=fecha_nacimiento,
                        direccion=direccion,
                        sexo=sexo
                    )

                    grupo, _ = Group.objects.get_or_create(name=cargo)
                    profile.groups.add(grupo)

                    usuarios_creados += 1

                except Exception as e:
                    messages.warning(request, f"Fila {fila}: Error inesperado - {str(e)}")
                    usuarios_omitidos += 1
                    continue

            messages.success(
                request,
                f"Carga completada. {usuarios_creados} usuarios creados, {usuarios_omitidos} filas omitidas por errores."
            )

        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar el archivo: {str(e)}")

        return redirect('lista_usuarios_activos')

    return redirect('lista_usuarios_activos')




# ------------------ DASHBOARD DE USUARIOS ------------------



@login_required
def dashboard_usuarios(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users

    percent_active = (active_users / total_users * 100) if total_users else 0
    percent_inactive = 100 - percent_active

    empleados_group = Group.objects.get(name="Empleado")
    administradores_group = Group.objects.get(name="Administrador")

    empleados = User.objects.filter(groups=empleados_group).count()
    administradores = User.objects.filter(groups=administradores_group).count()
    ambos = User.objects.annotate(num_groups=Count('groups')).filter(num_groups__gt=1).count()

    ultimo_usuario = User.objects.latest('date_joined')

    context = {
        'total_users': total_users,
        'percent_active': round(percent_active, 2),
        'percent_inactive': round(percent_inactive, 2),
        'empleados': empleados,
        'administradores': administradores,
        'ambos': ambos,
        'ultimo_usuario': ultimo_usuario,
    }

    return render(request, 'administrador/dashboard_usuarios.html', context)



# ------------------------------------ FIN GESTIÓN DE USUARIOS ------------------------------------



# ------------------------------------ GESTIÓN DE PROVEEDORES ------------------------------------



# ------------------ LISTADO DE PROVEEDORES ACTIVOS Y BLOQUEADOS ------------------



@login_required
def lista_proveedores_activos(request):
    order_by = request.GET.get('order_by', '')

    proveedores_activos = Proveedor.objects.filter(estado=True)

    if order_by:
        if order_by == 'nombre':
            proveedores = proveedores_activos.order_by('nombre')
        elif order_by == 'rut':
            proveedores = proveedores_activos.order_by('rut')
        else:
            proveedores = proveedores_activos
    else:
        proveedores = proveedores_activos
    
    paginator = Paginator(proveedores, 10)
    page_number = request.GET.get('page')
    proveedores = paginator.get_page(page_number)

    return render(request, 'administrador/lista_proveedores.html', {'proveedores': proveedores, 'order_by': order_by})



@login_required
def lista_proveedores_bloqueados(request):
    order_by = request.GET.get('order_by', '')

    proveedores_bloqueados = Proveedor.objects.filter(estado=False)

    if order_by:
        if order_by == 'nombre':
            proveedores = proveedores_bloqueados.order_by('nombre')
        elif order_by == 'rut':
            proveedores = proveedores_bloqueados.order_by('rut')
        else:
            proveedores = proveedores_bloqueados 
    else:
        proveedores = proveedores_bloqueados  

    paginator = Paginator(proveedores, 10)
    page_number = request.GET.get('page')
    proveedores = paginator.get_page(page_number)

    return render(request, 'administrador/lista_proveedores_bloqueados.html', {'proveedores': proveedores, 'order_by': order_by})



# ------------------ AGREGAR - MOSTRAR - EDITAR - ACTIVAR - BLOQUEAR ------------------



def agregar_proveedor(request):
    if request.method == 'POST':
        form = CrearProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            return redirect('mostrar_proveedor', proveedor_id=proveedor.id)
    else:
        form = CrearProveedorForm()
    
    return render(request, 'administrador/agregar_proveedor.html', {'form': form})



@require_POST
@login_required
def activar_proveedor(request):
    try:
        proveedor_id = request.POST.get('proveedor_id')
        proveedor_ids = json.loads(request.POST.get('proveedor_ids', '[]')) if request.POST.get('proveedor_ids') else []

        if proveedor_id:
            proveedor_ids = [int(proveedor_id)]

        proveedor_ids = [int(uid) for uid in proveedor_ids]
        proveedores = Proveedor.objects.filter(id__in=proveedor_ids, estado=False)

        updated_count = 0
        for proveedor in proveedores:
            proveedor.estado = True
            proveedor.save()
            updated_count += 1

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    


@require_POST
@login_required
def bloquear_proveedor(request):
    try:
        proveedor_id = request.POST.get('proveedor_id')
        proveedor_ids = json.loads(request.POST.get('proveedor_ids', '[]')) if request.POST.get('proveedor_ids') else []

        if proveedor_id:
            proveedor_ids = [proveedor_id]

        proveedor_ids = [int(uid) for uid in proveedor_ids]
        proveedores = Proveedor.objects.filter(id__in=proveedor_ids, estado=True)
        updated_count = proveedores.update(estado=False)

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    


@login_required
def mostrar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    return render(request, 'administrador/mostrar_proveedor.html', {'proveedor': proveedor})    



@login_required
def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)

    if request.method == 'POST':
        form = EditarProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = EditarProveedorForm(instance=proveedor)
        return render(request, 'administrador/editar_proveedor.html', {
            'proveedor_form': form,
            'proveedor': proveedor
        })



def asignar_productos(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    order_by = request.GET.get('order_by', 'nombre')

    productos = Producto.objects.filter(activo=True).order_by(order_by)

    if request.method == 'POST':
        ids_productos_seleccionados = request.POST.getlist('productos[]')
        ids_productos_seleccionados = list(map(int, ids_productos_seleccionados))

        proveedor.productos.set(ids_productos_seleccionados)

        return redirect('mostrar_proveedor', proveedor_id=proveedor.id)

    context = {
        'proveedor': proveedor,
        'productos': productos,
        'order_by': order_by,
        'productos_asignados_ids': proveedor.productos.values_list('id', flat=True),
    }
    return render(request, 'administrador/asignar_producto_proveedor.html', context)



# ------------------ DASHBOARD DE PROVEEDORES ------------------



@login_required
def dashboard_proveedores(request):
    total_proveedores = Proveedor.objects.count()
    proveedores_activos = Proveedor.objects.filter(estado=True).count()
    proveedores_bloqueados = total_proveedores - proveedores_activos

    percent_activos = (proveedores_activos / total_proveedores * 100) if total_proveedores else 0
    percent_bloqueados = 100 - percent_activos if total_proveedores else 0

    try:
        ultimo_proveedor = Proveedor.objects.latest('fecha_creacion')
    except ObjectDoesNotExist:
        ultimo_proveedor = None

    context = {
        'total_proveedores': total_proveedores,
        'percent_activos': round(percent_activos, 2),
        'percent_bloqueados': round(percent_bloqueados, 2),
        'ultimo_proveedor': ultimo_proveedor,
    }

    return render(request, 'administrador/dashboard_proveedores.html', context)



# ------------------------------------ CARGA MASIVA DE PROVEEDORES ------------------------------------



@login_required
@require_POST
@require_POST
def carga_masiva_proveedores(request):
    form = CargaMasivaProveedorForm(request.POST, request.FILES)

    if form.is_valid():
        archivo = request.FILES['archivo']
        try:
            # Leer archivo
            if archivo.name.endswith('.xlsx'):
                df = pd.read_excel(archivo)
            elif archivo.name.endswith('.csv'):
                df = pd.read_csv(archivo)
            else:
                messages.error(request, "Formato no soportado. Usa .xlsx o .csv.")
                return redirect('lista_proveedores_activos')

            columnas_requeridas = ['nombre', 'rut', 'telefono', 'correo', 'direccion']
            if not all(col in df.columns for col in columnas_requeridas):
                messages.error(request, "Faltan columnas requeridas.")
                return redirect('lista_proveedores_activos')

            errores, nuevos = [], 0

            for index, row in df.iterrows():
                fila = index + 2  # Excel: fila 1 = encabezado

                nombre = str(row['nombre']).strip()
                rut = str(row['rut']).strip()
                telefono = str(row.get('telefono', '')).strip()
                correo = str(row['correo']).strip()
                direccion = str(row.get('direccion', '')).strip()

                # Validaciones personalizadas
                if not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", rut):
                    errores.append(f"Fila {fila}: RUT inválido ({rut}). Formato: XX.XXX.XXX-X")
                    continue

                if Proveedor.objects.filter(rut=rut).exists():
                    errores.append(f"Fila {fila}: RUT {rut} ya está registrado.")
                    continue

                if re.search(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]", nombre):
                    errores.append(f"Fila {fila}: Nombre inválido. Solo letras y espacios.")
                    continue

                if not re.match(r"^\d\s\d{4}\s\d{4}$", telefono):
                    errores.append(f"Fila {fila}: Teléfono inválido ({telefono}). Formato: 9 8765 4321")
                    continue

                if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", correo):
                    errores.append(f"Fila {fila}: Correo inválido ({correo})")
                    continue

                # Crear proveedor
                proveedor = Proveedor(
                    nombre=nombre,
                    rut=rut,
                    telefono=telefono,
                    correo=correo,
                    direccion=direccion,
                    estado=True
                )
                proveedor.save()
                nuevos += 1

            if nuevos:
                messages.success(request, f"{nuevos} proveedores cargados correctamente.")
            if errores:
                for e in errores:
                    messages.warning(request, e)

        except Exception as e:
            messages.error(request, f"Error al procesar archivo: {str(e)}")
    else:
        messages.error(request, "Formulario inválido. Sube un archivo válido.")

    return redirect('lista_proveedores_activos')



# ------------------------------------ FIN GESTIÓN DE PROVEEDORES ------------------------------------



# ------------------------------------  GESTIÓN DE COMPRAS ------------------------------------



# ------------------ LISTADO DE COMPRAS ACTIVAS Y BLOQUEADAS ------------------



@login_required
def lista_compras_activas(request):
    order_by = request.GET.get('order_by', '')

    compras_activas = Compra.objects.filter(activo=True)

    if order_by:
        if order_by == 'proveedor':
            compras = compras_activas.order_by('proveedor')
        elif order_by == 'usuario':
            compras = compras_activas.order_by('usuario')
    else:
        compras = compras_activas.order_by('-id')
    
    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')
    compras = paginator.get_page(page_number)

    return render(request, 'administrador/lista_compras.html', {'compras': compras, 'order_by': order_by})



@login_required
def lista_compras_bloqueadas(request):
    order_by = request.GET.get('order_by', '')

    compras_bloqueadas = Compra.objects.filter(activo=False)

    if order_by:
        if order_by == 'proveedor':
            compras = compras_bloqueadas.order_by('proveedor')
        elif order_by == 'usuario':
            compras = compras_bloqueadas.order_by('usuario')
        else:
            compras = compras_bloqueadas.order_by('')
    else:
        compras = compras_bloqueadas.order_by('-id') 

    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')
    compras = paginator.get_page(page_number)

    return render(request, 'administrador/lista_compras_bloqueadas.html', {'compras': compras, 'order_by': order_by})



# ------------------ REGISTRAR - MOSTRAR - APROBAR - CANCELAR ------------------



@login_required
def registrar_compra_view(request):
    DetalleFormSet = formset_factory(DetalleCompraForm, extra=1, can_delete=True)
    
    try:
        proveedor_id = int(request.POST.get('proveedor') or request.GET.get('proveedor'))
        proveedor = Proveedor.objects.filter(id=proveedor_id).first()
    except (TypeError, ValueError):
        proveedor_id = None
        proveedor = None

    if request.method == 'POST' and 'submit' in request.POST:
        compra_form = CompraForm(request.POST)
        detalle_formset = DetalleFormSet(request.POST)
        
        if not proveedor:
            compra_form.add_error('proveedor', 'No se puede registrar una compra. Primero cargue los datos del proveedor y seleccione los productos que desea.')
            return render(request, 'administrador/registrar_compra.html', {
                'compra_form': compra_form,
                'detalle_formset': detalle_formset,
                'proveedor_seleccionado': proveedor,
            })


        for form in detalle_formset:
            form.fields['producto'].queryset = proveedor.productos.filter(activo=True) if proveedor else Producto.objects.none()

        if compra_form.is_valid() and detalle_formset.is_valid():
            productos_vistos = set()
            error_repetido = False

            formularios_validos = []

            for form in detalle_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    producto = form.cleaned_data['producto']

                    if producto in productos_vistos:
                        form.add_error('producto', 'Este producto ya fue ingresado.')
                        error_repetido = True
                    else:
                        productos_vistos.add(producto)
                        formularios_validos.append(form)
            if not formularios_validos:
                detalle_formset.non_form_errors = lambda: ['Debe agregar al menos un producto para registrar la compra.']
                return render(request, 'administrador/registrar_compra.html', {
                    'compra_form': compra_form,
                    'detalle_formset': detalle_formset,
                    'proveedor_seleccionado': proveedor,
                })

            productos_disponibles = proveedor.productos.filter(activo=True).count()
            if len(formularios_validos) > productos_disponibles:
                for form in detalle_formset:
                    form.add_error(None, "Se han ingresado más productos de los disponibles para este proveedor.")
                return render(request, 'administrador/registrar_compra.html', {
                    'compra_form': compra_form,
                    'detalle_formset': detalle_formset,
                    'proveedor_seleccionado': proveedor,
                })

            if error_repetido:
                return render(request, 'administrador/registrar_compra.html', {
                    'compra_form': compra_form,
                    'detalle_formset': detalle_formset,
                    'proveedor_seleccionado': proveedor,
                })

            compra = Compra.objects.create(
                proveedor=compra_form.cleaned_data['proveedor'],
                usuario=request.user,
                estado='Pendiente'
            )

            productos_solicitados = []

            for form in formularios_validos:
                producto = form.cleaned_data['producto']
                cantidad = form.cleaned_data['cantidad']
                observaciones = form.cleaned_data.get('observaciones', '')

                DetalleCompra.objects.create(
                    compra=compra,
                    producto=producto,
                    cantidad=cantidad,
                    observaciones=observaciones
                )

                texto = f"- {producto.nombre}: {cantidad} unidades"
                if observaciones:
                    texto += f" Nota: {observaciones}"

                productos_solicitados.append(texto)

            mensaje = f"""
                Estimado/a {proveedor.nombre},

                Le informamos que se ha registrado una nueva solicitud de compra con los siguientes productos:

                {chr(10).join(productos_solicitados)}

                Atentamente,
                ComercialJM
            """

            send_mail(
                subject="Nueva solicitud de compra",
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[proveedor.correo],
                fail_silently=False,
            )

            return redirect('lista_compras_activas')

    else:
        compra_form = CompraForm(initial={'proveedor': proveedor_id})
        detalle_formset = DetalleFormSet()

        for form in detalle_formset:
            form.fields['producto'].queryset = proveedor.productos.filter(activo=True) if proveedor else Producto.objects.none()

    return render(request, 'administrador/registrar_compra.html', {
        'compra_form': compra_form,
        'detalle_formset': detalle_formset,
        'proveedor_seleccionado': proveedor,
    })




@csrf_exempt
def aprobar_compra(request):
    if request.method == 'POST':
        compra_id = request.POST.get('compra_id')
        compra = get_object_or_404(Compra, id=compra_id)

        if compra.estado != 'Pendiente':
            return JsonResponse({
                'success': False,
                'message': 'La compra ya fue procesada.'
            })

        # Usar el formulario para validar el total
        form = AprobarCompraForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()  # Guarda el total

            compra.estado = 'Lista'
            compra.activo = False
            compra.save()

            numero_lote = str(uuid.uuid4())[:8]
            lote = Lote.objects.create(numero=numero_lote)

            for detalle in compra.detalles.all():
                producto = detalle.producto
                cantidad = detalle.cantidad

                DetalleLote.objects.create(
                    lote=lote,
                    producto=producto.nombre,
                    cantidad=cantidad,
                    precio=producto.precio
                )

                producto.cantidad += cantidad
                producto.lote = lote
                producto.save()

            return JsonResponse({
                'success': True,
                'message': 'Compra aprobada y lote creado correctamente.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Formulario inválido: asegúrate de ingresar un total válido.'
            })

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })


@require_POST
def bloquear_compra(request):
    compra_id = request.POST.get('compra_id')

    try:
        compra = Compra.objects.get(id=compra_id)
        compra.estado = 'Cancelada'
        compra.activo = False
        compra.save()
        return JsonResponse({'success': True})
    except Compra.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Compra no encontrada'})
    

def detalle_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    return render(request, 'administrador/detalle_compra.html', {'compra': compra})



# ------------------ DASHBOARD DE COMPRAS ------------------




@login_required
def dashboard_compras(request):
    ultima_compra = Compra.objects.order_by('-fecha').first()

    proveedor_mas_compras = (
        Compra.objects.values('proveedor__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )

    estado_data_raw = Compra.objects.values('estado').annotate(cantidad=Count('estado'))
    estado_data = {}

    for estado in estado_data_raw:
        nombre_estado = estado['estado'].capitalize()
        estado_data[nombre_estado] = estado['cantidad']

    total_estados = sum(estado_data.values())

    orden_deseado = ['Pendiente', 'Lista', 'Cancelada']
    colores_estado = {
        'Pendiente': 'yellow',
        'Lista': 'green',
        'Cancelada': 'red',
    }

    estado_chart_data = []
    for estado in orden_deseado:
        porcentaje = round((estado_data.get(estado, 0) / total_estados) * 100, 2) if total_estados > 0 else 0
        estado_chart_data.append({
            'estado': estado,
            'porcentaje': porcentaje,
            'color': colores_estado.get(estado, '#ccc'),
        })

    # Top productos
    top_productos = (
        DetalleCompra.objects
        .values('producto__nombre')
        .annotate(total_cantidad=Count('producto'))
        .order_by('-total_cantidad')[:3]
    )

    context = {
        'ultima_compra': ultima_compra,
        'proveedor_mas_compras': proveedor_mas_compras,
        'estado_chart_data': estado_chart_data,
        'top_productos': top_productos,
    }

    return render(request, 'administrador/dashboard_compras.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from registration.models import Producto, DetalleLote, Merma, DetalleVenta, Lote
from .forms import ProductoForm
from django.db import models
from django.db.models import Sum
from registration.models import Producto
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from . import views


productos = Producto.objects.filter(activo=True).annotate(
    total_cantidad=Sum('detalles_lote__cantidad')
)


def listar_productos(request):
    query = request.GET.get("q", "").strip()

    productos_queryset = Producto.objects.filter(activo=True).annotate(
        cantidad_sumada=Sum('detalles_lote__cantidad')  # <- usa este nombre
    ).order_by('nombre')

    if query:
        productos_queryset = productos_queryset.filter(nombre__icontains=query)

    paginator = Paginator(productos_queryset, 5)
    page_number = request.GET.get("page")
    productos = paginator.get_page(page_number)

    return render(request, 'administrador/listar_productos.html', {
        'productos': productos,
        'query': query
    })




def productos_inactivos(request):
    query = request.GET.get("q", "").strip()

    productos_queryset = Producto.objects.filter(activo=False).annotate(
        cantidad_sumada=Sum('detalles_lote__cantidad')
    ).order_by('nombre')

    if query:
        productos_queryset = productos_queryset.filter(nombre__icontains=query)

    paginator = Paginator(productos_queryset, 5)
    page_number = request.GET.get("page")
    productos = paginator.get_page(page_number)

    return render(request, 'administrador/listar_productos_inactivos.html', {
        'productos': productos,
        'query': query
    })


def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.activo = True

            # Campos que no se muestran en el HTML, asígnalos tú:
            producto.unidad_medida = 'kg'  # o el valor por defecto
            producto.precio_caja = 0.00
            producto.contenido_por_caja = 1.0

            producto.save()
            return redirect('listar_productos')
        else:
            print("❌ Errores del formulario:", form.errors)
    else:
        form = ProductoForm()
    return render(request, 'administrador/form_producto.html', {'form': form, 'titulo': 'Agregar Producto'})




def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    page = request.GET.get('page') or request.POST.get('page') or '1'


    if request.method == 'POST':
        data = request.POST.copy()

        # Rellenar el precio con el valor actual si viene vacío
        if not data.get('precio_venta'):
            data['precio_venta'] = producto.precio_venta  

        form = ProductoForm(data, instance=producto)

        if form.is_valid():
            form.save()
            return redirect(f'{reverse("listar_productos")}?page={page}')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'administrador/editar_producto.html', {
        'form': form,
        'producto': producto,
        'page': page,
    })



def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    page = request.GET.get("page", "1")
    producto.delete()
    return redirect(f"{reverse('listar_productos')}?page={page}")


def toggle_estado_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.activo = not producto.activo
    producto.save()
    if producto.activo:
        messages.success(request, "Producto activado con éxito.")
    else:
        messages.warning(request, "Producto desactivado con éxito.")
    origen = request.GET.get('origen', 'activos')
    return redirect('productos_inactivos' if origen == 'inactivos' else 'listar_productos')

def ver_lotes_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    lotes = Lote.objects.filter(producto=producto)  
    return render(request, 'administrador/lotes_por_producto.html', {
        'producto': producto,
        'lotes': lotes,
    })

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Sum
from registration.models import Producto

def buscar_productos_ajax(request):
    query = request.GET.get("q", "").strip()

    productos_queryset = Producto.objects.filter(activo=True, nombre__icontains=query).annotate(
        cantidad_sumada=Sum('detalles_lote__cantidad')  # <- mismo nombre aquí
    ).order_by('nombre')

    paginator = Paginator(productos_queryset, 5)
    page_number = request.GET.get("page")
    productos = paginator.get_page(page_number)

    tabla_html = render_to_string('administrador/partials/tabla_productos.html', {
        'productos': productos,
        'query': query,
    })

    return JsonResponse({'tabla_html': tabla_html})


def buscar_productos_inactivos_ajax(request):
    query = request.GET.get("q", "").strip()

    productos_queryset = Producto.objects.filter(
        activo=False,
        nombre__icontains=query
    ).annotate(
        cantidad_sumada=Sum('detalles_lote__cantidad')
    ).order_by('nombre')

    paginator = Paginator(productos_queryset, 5)
    page_number = request.GET.get("page")
    productos = paginator.get_page(page_number)

    tabla_html = render_to_string('administrador/partials/tabla_productos.html', {
        'productos': productos,
        'query': query,
    })

    return JsonResponse({'tabla_html': tabla_html})




from django.db.models import Sum  
from collections import defaultdict
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from registration.models import Producto, DetalleLote, Merma

def lotes_por_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    lotes_dict = defaultdict(lambda: {
        'cantidad_inicial': 0,
        'mermadas': 0,
        'disponibles': 0,
        'fecha': None
    })

    detalles_lotes = DetalleLote.objects.filter(producto=producto)

    for detalle in detalles_lotes:
        lote = detalle.lote
        lote_key = lote.numero  

        lotes_dict[lote_key]['cantidad_inicial'] += detalle.cantidad
        lotes_dict[lote_key]['fecha'] = lote.fecha

    for lote_numero in lotes_dict:
        mermadas = Merma.objects.filter(producto=producto, lote=lote_numero).aggregate(
            total=Sum('cantidad')
        )['total'] or 0

        disponibles = lotes_dict[lote_numero]['cantidad_inicial'] - mermadas

        lotes_dict[lote_numero]['mermadas'] = mermadas
        lotes_dict[lote_numero]['disponibles'] = disponibles

    datos = [
        {
            'lote': lote_numero,
            'fecha': info['fecha'],
            'cantidad_inicial': info['cantidad_inicial'],
            'mermadas': info['mermadas'],
            'disponibles': info['disponibles']
        }
        for lote_numero, info in lotes_dict.items()
    ]

    return render(request, 'administrador/lotes_por_producto.html', {
        'producto': producto,
        'datos': datos
    })






# ------------------------------------ GESTIÓN DE LOTES ------------------------------------

from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from registration.models import Lote, DetalleLote

def listar_lotes(request):
    lotes = Lote.objects.all().order_by('-fecha')
    
    # Aplicar filtros si existen en la URL
    numero_lote = request.GET.get('numero')
    fecha = request.GET.get('fecha')
    
    if numero_lote:
        lotes = lotes.filter(numero__icontains=numero_lote)
    
    if fecha:
        lotes = lotes.filter(fecha=fecha)
    
    # Paginación
    paginator = Paginator(lotes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'administrador/listar_lotes.html', {'lotes': page_obj})


def ver_lote(request, id):
    lote = get_object_or_404(Lote, id=id)

    detalles_crudos = DetalleLote.objects.select_related('producto').filter(lote=lote)

    productos_agregados = {}

    for detalle in detalles_crudos:
        producto = detalle.producto
        pid = producto.id

        if pid not in productos_agregados:
            productos_agregados[pid] = {
                'producto': producto,
                'cantidad': 0,
                'precio': detalle.precio
            }

        productos_agregados[pid]['cantidad'] += detalle.cantidad

    detalles = [
        {
            'producto': data['producto'],
            'cantidad': data['cantidad'],
            'precio': data['precio']
        }
        for data in productos_agregados.values()
    ]

    return render(request, 'administrador/ver_lote.html', {
        'lote': lote,
        'detalles': detalles
    })

def eliminar_lote(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)
    lote.delete()
    messages.success(request, 'Lote eliminado correctamente.')
    return redirect('listar_lotes')


def carga_excel_lotes(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        print("→ Método POST recibido")
        archivo = request.FILES['archivo_excel']

        try:
            df_raw = pd.read_excel(archivo, header=None, engine='openpyxl')
            print("→ Columnas detectadas:", df_raw.columns.tolist())
            print("→ Primeras filas:")
            print(df_raw.head())
        except Exception as e:
            messages.error(request, f'Error al leer el archivo: {e}')
            return redirect('listar_lotes')

        columnas_esperadas = {'producto', 'cantidad', 'precio'}
        indice_encabezado = None

        for i, fila in df_raw.iterrows():
            encabezados_normalizados = set()
            for valor in fila:
                if pd.notna(valor):
                    nombre = str(valor).strip().lower().rstrip('s') 
                    encabezados_normalizados.add(nombre)
            if columnas_esperadas.issubset(encabezados_normalizados):
                indice_encabezado = i
                break

        if indice_encabezado is None:
            messages.error(request, 'No se encontraron columnas válidas: producto, cantidad, precio.')
            return redirect('listar_lotes')
        try:
            df = pd.read_excel(archivo, header=indice_encabezado, engine='openpyxl')
            df.columns = [str(c).strip().lower().rstrip('s') for c in df.columns]
            df = df[['producto', 'cantidad', 'precio']]
        except Exception as e:
            messages.error(request, f'Error al procesar columnas: {e}')
            return redirect('listar_lotes')

        fecha_actual = timezone.now().date()
        lote, _ = Lote.objects.get_or_create(
            fecha=fecha_actual,
            defaults={'numero': f"L-{Lote.objects.count() + 1:03d}"}
        )

        productos_cargados = 0

        for _, row in df.iterrows():
            try:
                nombre = str(row['producto']).strip().replace('\n', ' ').replace('\r', '')
                cantidad = int(row['cantidad'])
                precio = float(row['precio'])

                producto, _ = Producto.objects.get_or_create(
                    nombre__iexact=nombre,
                    defaults={
                        'nombre': nombre,
                        'tipo': 'Otros',  # o lo que corresponda
                        'unidad_medida': 'unidad',
                        'precio_venta': precio,
                        'precio_caja': precio,
                        'contenido_por_caja': 1,
                        'activo': True
                    }
)


                DetalleLote.objects.create(
                    lote=lote,
                    producto=producto,
                    cantidad=cantidad,
                    precio=precio
                )

                productos_cargados += 1

            except Exception as e:
                print(f"⛔ Error al procesar fila: {row} → {e}")
                continue

        if productos_cargados == 0:
            messages.warning(request, 'No se cargaron productos. Revisa el contenido del archivo.')
        else:
            messages.success(request, f'Se cargaron {productos_cargados} productos correctamente.')

        return redirect('listar_lotes')

    messages.error(request, 'No se proporcionó un archivo válido.')
    return redirect('listar_lotes')


import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font

def descargar_plantilla_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plantilla Lotes"

    # Encabezados
    columnas = ['Producto', 'Cantidad', 'Precio']
    for i, encabezado in enumerate(columnas, 1):
        celda = ws.cell(row=1, column=i, value=encabezado)
        celda.font = Font(bold=True)

    # Respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=plantilla_lotes.xlsx'
    wb.save(response)
    return response



# ------------------------------------ GESTIÓN DE MERMAS ------------------------------------



def listar_mermas(request):
    mermas = Merma.objects.filter(activo=True)
    return render(request, 'administrador/listar_mermas.html', {'mermas': mermas})

def agregar_merma(request):
    if request.method == 'POST':
        form = MermaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_mermas')
    else:
        form = MermaForm()
    return render(request, 'administrador/form_merma.html', {'form': form, 'titulo': 'Agregar Merma'})



# ------------------------------------ GESTIÓN DE CLIENTES ------------------------------------



def listar_clientes_activos(request):
    clientes = Cliente.objects.filter(activo=True)
    return render(request, 'administrador/listar_clientes_activos.html', {'clientes': clientes})

def listar_clientes_inactivos(request):
    clientes = Cliente.objects.filter(activo=False)
    return render(request, 'administrador/listar_clientes_inactivos.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.activo = True
            cliente.save()
            return redirect('listar_clientes_activos')
        else:
            print("Errores del formulario:", form.errors) 
    else:
        form = ClienteForm()

    return render(request, 'administrador/crear_cliente.html', {'form': form})


def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.delete()
    return redirect('listar_clientes_activos')

def toggle_estado_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.activo = not cliente.activo  
    cliente.save()

    if cliente.activo:
        return redirect('listar_clientes_inactivos')
    else:
        return redirect('listar_clientes_activos')
    
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from registration.models import Cliente
from registration.models import Venta

def ranking_clientes(request):
    q = request.GET.get('q', '')

    clientes = Cliente.objects.filter(activo=True)

    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(rut__icontains=q) |
            Q(categoria__icontains=q)
        )

    clientes = clientes.annotate(
        total_ventas=Sum('ventas__total'),
        cantidad_ventas=Count('ventas')
    ).order_by('-cantidad_ventas')

    return render(request, 'administrador/ranking_clientes.html', {
        'clientes': clientes
    })


def dashboard_clientes(request):
    total_clientes = Cliente.objects.count()
    activos = Cliente.objects.filter(activo=True).count()
    inactivos = total_clientes - activos
    percent_activos = round((activos / total_clientes) * 100, 2) if total_clientes else 0
    percent_inactivos = round((inactivos / total_clientes) * 100, 2) if total_clientes else 0

    categorias = list(Cliente.objects.values_list('categoria', flat=True).distinct())
    cantidades = [Cliente.objects.filter(categoria=cat).count() for cat in categorias]

    ultimo_cliente = Cliente.objects.order_by('-id').first()

    context = {
        'total_clientes': total_clientes,
        'percent_activos': percent_activos,
        'percent_inactivos': percent_inactivos,
        'categorias': categorias,
        'cantidades': cantidades,
        'ultimo_cliente': ultimo_cliente
    }
    return render(request, 'administrador/dashboard_clientes.html', context)


def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes_activos')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'administrador/editar_clientes.html', {'form': form})




def dashboard_productos(request):
    total_productos = Producto.objects.count()
    activos = Producto.objects.filter(activo=True).count()
    inactivos = total_productos - activos
    productos_con_merma = Merma.objects.values('producto').distinct().count()
    porcentaje_mermas = (productos_con_merma / total_productos * 100) if total_productos else 0
    tipos_data = Producto.objects.values('tipo').annotate(total=Count('id'))
    ultimo_producto = Producto.objects.latest('fecha')

    context = {
        'total_productos': total_productos,
        'percent_activos': round((activos / total_productos) * 100) if total_productos else 0,
        'percent_inactivos': round((inactivos / total_productos) * 100) if total_productos else 0,
        'percent_mermas': round(porcentaje_mermas),
        'tipos': [tipo['tipo'] for tipo in tipos_data],
        'cantidades': [tipo['total'] for tipo in tipos_data],
        'ultimo_producto': ultimo_producto,
    }
    return render(request, 'administrador/dashboard_productos.html', context)

def debug_url_test(request):
    try:
        url = reverse('eliminar_producto', kwargs={'id': 1})
        return HttpResponse(f"✅ URL encontrada: {url}")
    except Exception as e:
        return HttpResponse(f"❌ Error: {e}")



import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from registration.models import Cliente, Cupon


def generar_cupon_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            descuento = data.get('descuento')

            if not cliente_id or not descuento:
                return JsonResponse({'status': 'error', 'mensaje': 'Datos incompletos'}, status=400)

            cliente = Cliente.objects.get(pk=cliente_id)
            cupon = Cupon.objects.create(
                cliente=cliente,
                descuento=int(descuento),
                usado=False
            )

            return JsonResponse({'status': 'ok', 'mensaje': f'Cupón del {descuento}% generado para {cliente.nombre}'})
        
        except Cliente.DoesNotExist:
            return JsonResponse({'status': 'error', 'mensaje': 'Cliente no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)


# ------------------------------------ GESTIÓN DE VENTAS ------------------------------------

from django.shortcuts import render, redirect, get_object_or_404
from registration.models import Producto, Venta, DetalleVenta
from .forms import AgregarProductoVentaForm, VentaForm
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.utils import timezone
import json
from registration.models import Cupon  
from decimal import Decimal


def dashboard_ventas(request):
    total_ventas = Venta.objects.aggregate(total=Sum('total'))['total'] or 0
    ventas_dia = Venta.objects.filter(fecha__date=timezone.localdate()).aggregate(total=Sum('total'))['total'] or 0
    productos_vendidos = DetalleVenta.objects.aggregate(total=Sum('cantidad'))['total'] or 0

    ventas_por_categoria = (
        DetalleVenta.objects
        .select_related('producto')
        .values('producto__tipo')
        .annotate(total=Sum('subtotal'))
        .order_by('-total')
    )

    categorias_ventas = [item['producto__tipo'] for item in ventas_por_categoria]
    montos_ventas = [float(item['total']) for item in ventas_por_categoria]

    pagos_por_metodo = (
        Venta.objects
        .values('metodo_pago')
        .annotate(total=Count('id'))
    )

    labels_pago = [item['metodo_pago'] for item in pagos_por_metodo]
    valores_pago = [item['total'] for item in pagos_por_metodo]

    ultima_venta = Venta.objects.last()

    context = {
        'total_ventas': total_ventas,
        'ventas_dia': ventas_dia,
        'productos_vendidos': productos_vendidos,
        'categorias_ventas': json.dumps(categorias_ventas),
        'montos_ventas': json.dumps(montos_ventas),
        'labels_pago': json.dumps(labels_pago),
        'medios_pago': json.dumps(valores_pago),
        'ultima_venta': ultima_venta
    }

    return render(request, 'administrador/dashboard_ventas.html', context)

from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .forms import UnidadVentaForm
from registration.models import Producto, Cliente, Cupon, DetalleVenta, Venta
from .forms import VentaForm

def crear_venta(request):
    productos_disponibles = Producto.objects.filter(activo=True)
    cupones_disponibles = []
    venta_productos = request.session.get('venta_productos', [])
    productos = []
    total = 0
    mensaje_error = None
    descuento_aplicado = 0
    monto_descuento = 0
    total_con_descuento = total
    cupon_aplicado = None

    unidad_form = UnidadVentaForm(request.POST or None)

    cliente_id_url = request.GET.get("cliente")
    cliente_inicial = Cliente.objects.filter(id=cliente_id_url).first() if cliente_id_url else None

    if 'cupon_id' in request.POST:
        cupon_id = request.POST.get('cupon_id')
        cupon_id_int = None
        if cupon_id:
            try:
                cupon_id_clean = cupon_id.replace(',', '.')
                cupon_id_int = int(float(cupon_id_clean))
            except (ValueError, TypeError):
                cupon_id_int = None

        if cupon_id_int is not None:
            try:
                cupon = Cupon.objects.get(id=cupon_id_int, activo=True, usado=False)
                if cupon.valido_hasta and cupon.valido_hasta < timezone.now().date():
                    messages.error(request, "El cupón ha expirado")
                else:
                    descuento_aplicado = float(cupon.descuento)
                    monto_descuento = total * (descuento_aplicado / 100)
                    total_con_descuento = total - monto_descuento
                    cupon_aplicado = cupon.id
            except Cupon.DoesNotExist:
                messages.error(request, "Cupón no válido, ya usado o inactivo")


    if request.method == 'POST':
        form = VentaForm(request.POST)
    else:
        form = VentaForm(initial={'cliente': cliente_inicial}) if cliente_inicial else VentaForm()

    if form.is_valid():
        cliente = form.cleaned_data.get('cliente')
        if cliente:
            cupones_disponibles = Cupon.objects.filter(cliente=cliente, usado=False)
    elif cliente_inicial:
        cupones_disponibles = Cupon.objects.filter(cliente=cliente_inicial, usado=False)

    for item in venta_productos:
        try:
            producto = Producto.objects.get(id=item['producto_id'])
            cantidad = Decimal(str(item['cantidad']))
            unidad = item.get('unidad', 'unidad')  # default a unidad

            if unidad == 'caja':
                subtotal = producto.precio_caja * cantidad
                precio = producto.precio_caja
            else:
                subtotal = producto.precio_venta * cantidad
                precio = producto.precio_venta

            productos.append({
                'producto': producto,
                'cantidad': cantidad,
                'unidad': unidad,
                'precio': precio,
                'subtotal': subtotal,
            })
            total += subtotal
        except Producto.DoesNotExist:
            continue

    if request.method == 'POST':
        if 'agregar' in request.POST:
            try:
                nombre_producto = request.POST.get('producto', '').strip()
                cantidad = Decimal(request.POST.get('cantidad', '0'))
                unidad = request.POST.get('unidad', 'unidad')  
                producto = Producto.objects.get(nombre__iexact=nombre_producto, activo=True)

                if cantidad <= 0:
                    mensaje_error = "La cantidad debe ser mayor que 0."
                else:
                    venta_productos.append({
                        'producto_id': producto.id,
                        'cantidad': float(cantidad),
                        'unidad': unidad
                    })
                    request.session['venta_productos'] = venta_productos
                    return redirect('crear_venta')
            except (Producto.DoesNotExist, ValueError, TypeError):
                mensaje_error = "No hay existencias de este producto."

        elif 'eliminar_producto_id' in request.POST:
            producto_id = int(request.POST.get('eliminar_producto_id'))
            venta_productos = [p for p in venta_productos if p['producto_id'] != producto_id]
            request.session['venta_productos'] = venta_productos
            return redirect('crear_venta')
        
        elif 'cambiar_unidad' in request.POST:
            producto_id = int(request.POST.get('producto_id'))
            nueva_unidad = request.POST.get('cambiar_unidad')

            for item in venta_productos:
                if item['producto_id'] == producto_id:
                    item['unidad'] = nueva_unidad
                    break

            request.session['venta_productos'] = venta_productos
            return redirect('crear_venta')

        elif 'finalizar' in request.POST:
            cupon_id = request.POST.get('cupon_id')
            cupon_id_int = None
            if cupon_id:
                try:
                    cupon_id_clean = cupon_id.replace(',', '.')
                    cupon_id_int = int(float(cupon_id_clean))
                except (ValueError, TypeError, AttributeError):
                    cupon_id_int = None

            if form.is_valid() and productos:
                venta = form.save(commit=False)
                venta.total = total

                if cupon_id_int:
                    try:
                        cupon = Cupon.objects.get(id=cupon_id_int, cliente=venta.cliente, usado=False)
                        descuento = cupon.descuento
                        venta.total = total - (total * descuento / 100)
                        cupon.usado = True
                        cupon.save()
                    except Cupon.DoesNotExist:
                        pass

                venta.save()

                for item in productos:
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=item['producto'],
                        cantidad=item['cantidad'],
                        precio=item['precio'],
                        subtotal=item['subtotal'],
                        unidad=item['unidad']
                    )

                request.session['venta_productos'] = []
                return redirect('listar_ventas')


    context = {
        'venta_form': form,
        'unidad_form': unidad_form,
        'productos': productos,
        'total': total,
        'productos_disponibles': productos_disponibles,
        'mensaje_error': mensaje_error,
        'cupones_disponibles': cupones_disponibles,
        'descuento_aplicado': descuento_aplicado,
        'monto_descuento': monto_descuento,
        'total_con_descuento': total_con_descuento,
        'cupon_aplicado': cupon_aplicado,
    }
    return render(request, 'administrador/crear_venta.html', context)



def calcular_subtotal(producto, cantidad):
    if producto.unidad_medida == 'kg':
        return cantidad * producto.precio_kg
    else:
        return cantidad * producto.precio_unidad


def listar_ventas(request):
    ventas = Venta.objects.all().order_by('-fecha')
    return render(request, 'administrador/listar_ventas.html', {
        'ventas': ventas
    })

def detalle_venta(request, venta_id):
    venta = Venta.objects.get(id=venta_id)
    return render(request, 'administrador/detalle_venta.html', {
        'venta': venta
    })

def eliminar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    venta.delete()
    return redirect('listar_ventas')

from django.shortcuts import render, get_object_or_404
from registration.models import Cliente, Venta, DetalleVenta


def detalle_compras_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    ventas = Venta.objects.filter(cliente=cliente).prefetch_related('detalles', 'detalles__producto')

    return render(request, 'administrador/detalle_compras_cliente.html', {
        'cliente': cliente,
        'ventas': ventas
    })



# ------------------------------------ REPORTERIA ------------------------------------

def reporteria_view(request):
    filtro = request.GET.get('filtro', 'general')
    hoy = now().date()

    if filtro == 'diario':
        fecha_inicio = hoy
    elif filtro == 'semanal':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
    elif filtro == 'mensual':
        fecha_inicio = hoy.replace(day=1)
    elif filtro == 'anual':
        fecha_inicio = hoy.replace(month=1, day=1)
    else:
        fecha_inicio = None

    # Filtros condicionales
    filtro_fecha = {}
    if fecha_inicio:
        filtro_fecha['fecha__gte'] = fecha_inicio

    productos_activos = Producto.objects.filter(activo=True)
    detalles_lote = DetalleLote.objects.all()

    if fecha_inicio:
        detalles_lote = detalles_lote.filter(lote__fecha__gte=fecha_inicio)

    productos = []
    for producto in productos_activos:
        cantidad_total = detalles_lote.filter(producto=producto.nombre).aggregate(
            total=Sum('cantidad')
        )['total'] or 0

        productos.append({
            'nombre': producto.nombre,
            'cantidad': cantidad_total
        })

    compras_qs = Compra.objects.filter(activo=False, estado='Lista', **filtro_fecha)
    ventas_qs = Venta.objects.filter(**filtro_fecha)
    mermas_qs = Merma.objects.filter(activo=True, **filtro_fecha)

    compras_cantidad = compras_qs.count()
    ventas_cantidad = ventas_qs.count()
    mermas_cantidad = mermas_qs.count()

    compras_total = compras_qs.aggregate(total=Sum('total'))['total'] or 0
    ventas_total = ventas_qs.aggregate(total=Sum('total'))['total'] or 0
    mermas_total = sum([merma.precio * merma.cantidad for merma in mermas_qs])

    usuarios_activos = User.objects.filter(is_active=True).order_by('username')
    compras_por_usuario = []
    for usuario in usuarios_activos:
        user_compras = compras_qs.filter(usuario=usuario).count()
        compras_por_usuario.append({
            'username': usuario.username,
            'compras': user_compras
        })

    context = {
        'productos': list(productos),
        'data_cantidad': {
            'compras': compras_cantidad,
            'ventas': ventas_cantidad,
            'mermas': mermas_cantidad,
        },
        'data_total': {
            'compras': float(compras_total),
            'ventas': float(ventas_total),
            'mermas': float(mermas_total),
        },
        'compras_por_usuario': compras_por_usuario,
        'filtro': filtro,
    }
    return render(request, 'administrador/reporteria.html', context)


def reporteria_pdf_view(request):
    # Recolección de datos
    cantidad_compras = Compra.objects.count()
    cantidad_ventas = Venta.objects.count()
    cantidad_mermas = Merma.objects.count()

    total_compras = Compra.objects.aggregate(total=Sum('total'))['total'] or 0
    total_ventas = Venta.objects.aggregate(total=Sum('total'))['total'] or 0
    total_mermas = Merma.objects.aggregate(
        total=Sum(ExpressionWrapper(F('precio') * F('cantidad'), output_field=FloatField()))
    )['total'] or 0

    productos_con_lotes = Producto.objects.annotate(
        total_cantidad=Sum(
            'detallecompra__cantidad',
            filter=Q(detallecompra__compra__estado='Lista')
        )
    )

    compras_por_usuario = User.objects.annotate(
        total_compras=Count('compras')
    )

    # Obtener imágenes base64 del POST
    img_productos = request.POST.get('img_productos')
    img_torta_cantidad = request.POST.get('img_torta_cantidad')
    img_torta_total = request.POST.get('img_torta_total')
    img_compras_usuario = request.POST.get('img_compras_usuario')

    context = {
        'cantidad_compras': cantidad_compras,
        'cantidad_ventas': cantidad_ventas,
        'cantidad_mermas': cantidad_mermas,
        'total_compras': total_compras,
        'total_ventas': total_ventas,
        'total_mermas': total_mermas,
        'productos_con_lotes': productos_con_lotes,
        'compras_por_usuario': compras_por_usuario,

        # Las imágenes
        'img_productos': img_productos,
        'img_torta_cantidad': img_torta_cantidad,
        'img_torta_total': img_torta_total,
        'img_compras_usuario': img_compras_usuario,
    }

    template = get_template('administrador/reporteria_pdf.html')
    html_string = template.render(context)

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporteria.pdf"'
    return response