import csv
import json
from django.shortcuts import render, redirect
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
from registration.models import Profile, Proveedor, Compra
from datetime import datetime
from django.core.exceptions import ValidationError
from django.contrib import messages
from administrador.forms import EditUserProfileForm, CrearProveedorForm, EditarProveedorForm
from django.views.decorators.http import require_POST
from .forms import PerfilForm
from django.db.models import Count, Avg, Max, Min



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



@user_passes_test(lambda u: u.is_superuser)
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



@user_passes_test(lambda u: u.is_superuser)
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



def cargar_usuarios(request):
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo_csv = request.FILES["archivo"]
        try:
            decoded_file = archivo_csv.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            for row in reader:
                try:
                    required_fields = [
                        'rut', 'email', 'first_name', 'last_name',
                        'fecha_nacimiento', 'sexo', 'direccion', 'cargo', 'telefono'
                    ]
                    for field in required_fields:
                        if not row.get(field):
                            raise ValidationError(f"El campo '{field}' es obligatorio.")

                    if User.objects.filter(username=row['rut']).exists():
                        raise ValidationError(f"El usuario con RUT {row['rut']} ya existe.")

                    cargo = row['cargo'].strip().lower()
                    if cargo not in ['empleado', 'administrador']:
                        raise ValidationError(f"El cargo {row['cargo']} no es válido.")

                    grupo = Group.objects.get(name=cargo.capitalize())

                    user = User.objects.create_user(
                        username=row['rut'],
                        email=row['email'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        password='contraseña_default'
                    )
                    user.is_active = True
                    user.save()

                    profile = Profile.objects.create(
                        user=user,
                        rut=row['rut'],
                        fecha_nacimiento=convert_date(row['fecha_nacimiento']),
                        sexo=row['sexo'],
                        direccion=row['direccion'],
                        telefono=row['telefono']
                    )

                    # Asignar grupo al perfil y al usuario
                    profile.groups.add(grupo)
                    user.groups.add(grupo)
                    user.save()

                    print(f"[USUARIO CREADO] {user.username}")

                except ValidationError as e:
                    print(f"[VALIDATION ERROR] {e}")
                    messages.error(request, str(e))
                except Exception as e:
                    print(f"[ERROR] {row.get('rut', 'desconocido')}: {e}")
                    messages.error(request, f"Error al procesar usuario {row.get('rut', 'desconocido')}: {e}")

            messages.success(request, "Carga masiva completada.")
            return redirect("lista_usuarios_activos")

        except Exception as e:
            messages.error(request, f"Error al procesar archivo: {e}")
            return redirect("lista_usuarios_activos")

    return redirect("lista_usuarios_activos")



# Función para convertir las fechas al formato YYYY-MM-DD
def convert_date(date_str):
    try:
        # Convertir de 'DD/MM/YYYY' a 'YYYY-MM-DD'
        return datetime.strptime(date_str, '%d/%m/%Y').date()
    except ValueError:
        return None



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
            form.save()
            return redirect('lista_proveedores_activos')
    else:
        form = CrearProveedorForm()
    
    return render(request, 'administrador/agregar_proveedor.html', {'form': form})



@user_passes_test(lambda u: u.is_superuser)
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
    


@user_passes_test(lambda u: u.is_superuser)
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



# ------------------ DASHBOARD DE PROVEEDORES ------------------



@login_required
def dashboard_proveedores(request):
    total_proveedores = Proveedor.objects.count()
    proveedores_activos = Proveedor.objects.filter(estado=True).count()
    proveedores_bloqueados = total_proveedores - proveedores_activos

    percent_activos = (proveedores_activos / total_proveedores * 100) if total_proveedores else 0
    percent_bloqueados = 100 - percent_activos

    ultimo_proveedor = Proveedor.objects.latest('fecha_creacion')

    context = {
        'total_proveedores': total_proveedores,
        'percent_activos': round(percent_activos, 2),
        'percent_bloqueados': round(percent_bloqueados, 2),
        'ultimo_proveedor': ultimo_proveedor,
    }

    return render(request, 'administrador/dashboard_proveedores.html', context)



# ------------------------------------ FIN GESTIÓN DE PROVEEDORES ------------------------------------



# ------------------------------------  GESTIÓN DE COMPRAS ------------------------------------



# ------------------ LISTADO DE COMPRAS ACTIVAS Y BLOQUEADAS ------------------



@login_required
def lista_compras_activas(request):
    order_by = request.GET.get('order_by', '')

    compras_activas = Compra.objects.filter(activo=True)

    if order_by:
        if order_by == '':
            compras = compras_activas.order_by('')
        elif order_by == '':
            compras = compras_activas.order_by('')
        else:
            compras = compras_activas
    else:
        compras = compras_activas
    
    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')
    compras = paginator.get_page(page_number)

    return render(request, 'administrador/lista_compras.html', {'compras': compras, 'order_by': order_by})



@login_required
def lista_compras_bloqueadas(request):
    order_by = request.GET.get('order_by', '')

    compras_bloqueadas = Compra.objects.filter(activo=False)

    if order_by:
        if order_by == '':
            compras = compras_bloqueadas.order_by('')
        elif order_by == '':
            compras = compras_bloqueadas.order_by('')
        else:
            compras = compras_bloqueadas 
    else:
        compras = compras_bloqueadas  

    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')
    compras = paginator.get_page(page_number)

    return render(request, 'administrador/lista_compras_bloqueadas.html', {'compras': compras, 'order_by': order_by})



# ------------------ AGREGAR - MOSTRAR - EDITAR - ACTIVAR - BLOQUEAR ------------------



