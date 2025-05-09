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
import csv
from datetime import datetime
from django.core.exceptions import ValidationError
from django.contrib import messages




# Create your views here.
def pagina_prueba(request):
    return render(request, 'administrador/pagina_prueba.html')

def is_admin(user):
    return user.groups.filter(name='Administrador').exists()

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