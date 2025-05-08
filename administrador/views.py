from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator

# Create your views here.
def pagina_prueba(request):
    return render(request, 'administrador/pagina_prueba.html')

def is_admin(user):
    return user.groups.filter(name='Administrador').exists()

@login_required
def lista_usuarios(request):
    usuarios_list = User.objects.all().order_by('username')
    paginator = Paginator(usuarios_list, 10)

    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'administrador/lista_usuarios.html', {'usuarios': usuarios})