from django.shortcuts import render, redirect, get_object_or_404
from .forms import MermaForm
from django.contrib.auth.decorators import login_required
from .models import Merma
from core.models import Producto, Lote
from django.utils import timezone


@login_required
def dashboard(request):
    return render(request, 'administrador/dashboard.html')


def listar_mermas(request):
    productos = Merma.objects.all()
    return render(request, 'administrador/listar_mermas.html', {'productos': productos})


def eliminar_merma(request, id):
    merma = get_object_or_404(Merma, id=id)
    merma.delete()
    return redirect('listar_mermas')


def agregar_merma(request):
    if request.method == 'POST':
        form = MermaForm(request.POST)
        if form.is_valid():
            merma = form.save(commit=False)
            producto = merma.producto

            # Buscar lote activo asociado al producto seleccionado
            lote_qs = Lote.objects.filter(producto=producto, activo=True).order_by('-fecha')
            if lote_qs.exists():
                lote = lote_qs.first()
                merma.lote = lote.numero
                merma.fecha = lote.fecha
                merma.save()
                return redirect('listar_mermas')
            else:
                form.add_error(None, "⚠️ No se encontró lote activo para este producto.")
    else:
        form = MermaForm()
    
    return render(request, 'administrador/agregar_merma.html', {'form': form})