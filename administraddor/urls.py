from django.urls import path
from .views import dashboard, listar_mermas, eliminar_merma, agregar_merma
from .forms import MermaForm

urlpatterns = [
    path('', dashboard, name='dashboard'),  # ← ESTO ES LO QUE TE FALTA
    path('mermas/', listar_mermas, name='listar_mermas'),
    path('mermas/eliminar/<int:id>/', eliminar_merma, name='eliminar_merma'),
    path('mermas/agregar/', agregar_merma, name='agregar_merma'),
]

def agregar_merma(request):
    if request.method == 'POST':
        form = MermaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_mermas')
    else:
        form = MermaForm()
    return render(request, 'administrador/agregar_merma.html', {'form': form})




