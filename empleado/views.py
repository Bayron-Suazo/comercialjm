from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import PerfilForm

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

        return redirect('perfil_empleado')

    return render(request, 'empleado/perfil.html')