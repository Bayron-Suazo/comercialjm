from django.shortcuts import render

# Create your views here.
def pagina_prueba_empleado(request):
    return render(request, 'empleado/pagina_prueba_empleado.html')