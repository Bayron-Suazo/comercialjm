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
from registration.models import Profile
from datetime import datetime
from django.core.exceptions import ValidationError
from django.contrib import messages
from administrador.forms import EditUserProfileForm
from django.views.decorators.http import require_POST
from .forms import PerfilForm
from django.db.models import Count



# Create your views here.
@login_required
def lista_usuarios_activos(request):
    usuarios_list = User.objects.filter(is_active=True).order_by('username')
    paginator = Paginator(usuarios_list, 10)

    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'administrador/lista_usuarios.html', {'usuarios': usuarios})

@login_required
def lista_usuarios_bloqueados(request):
    usuarios_list = User.objects.filter(is_active=False).order_by('username')
    paginator = Paginator(usuarios_list, 10)

    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'administrador/lista_usuarios_bloqueados.html', {'usuarios': usuarios})

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

# Función para convertir las fechas al formato YYYY-MM-DD
def convert_date(date_str):
    try:
        # Convertir de 'DD/MM/YYYY' a 'YYYY-MM-DD'
        return datetime.strptime(date_str, '%d/%m/%Y').date()
    except ValueError:
        return None

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
        updated_count = users.update(is_active=True)

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
def mostrar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'administrador/mostrar_usuario.html', {'user': user})


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
    
@login_required
def perfil_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        profile.telefono = request.POST.get('telefono')
        profile.direccion = request.POST.get('direccion')
        profile.save()

        return redirect('perfil')

    return render(request, 'administrador/perfil.html')


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