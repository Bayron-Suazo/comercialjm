from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import PerfilForm



# ------------------ PERFIL USUARIO ------------------



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
            return render(request, 'empleado/perfil.html', {'user': user})

        # Si pasa validación, actualizar datos
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        profile.telefono = telefono
        profile.direccion = direccion
        profile.save()

        return redirect('perfil_empleado')

    return render(request, 'empleado/perfil.html', {'user': user})