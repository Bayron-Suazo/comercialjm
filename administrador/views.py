from django.shortcuts import render

# Create your views here.
def pagina_prueba(request):
    return render(request, 'administrador/pagina_prueba.html')