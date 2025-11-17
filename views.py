from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *
import json

@login_required
def dashboard(request):
    hoy = timezone.now().date()
    
    # Estadísticas del día
    ventas_hoy = Venta.objects.filter(fecha_venta__date=hoy)
    total_recaudado = ventas_hoy.aggregate(Sum('monto'))['monto__sum'] or 0
    
    context = {
        'total_ventas_hoy': ventas_hoy.count(),
        'total_recaudado_hoy': total_recaudado,
        'sorteos_hoy': ResultadoSorteo.objects.filter(fecha=hoy).count(),
    }
    return render(request, 'sistema/dashboard.html', context)

@login_required
def gestion_clientes(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sistema:gestion_clientes')
    else:
        form = ClienteForm()
    
    clientes = Cliente.objects.all().order_by('-fecha_registro')
    return render(request, 'sistema/clientes.html', {
        'form': form,
        'clientes': clientes
    })

@login_required
def realizar_venta(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.atendido_por = request.user
            venta.save()
            
            # Generar voucher (podrías redirigir a una vista de voucher)
            return redirect('voucher_venta', venta_id=venta.id)
    else:
        form = VentaForm()
    
    sorteos = Sorteo.objects.filter(activo=True)
    return render(request, 'sistema/venta.html', {
        'form': form,
        'sorteos': sorteos
    })

@login_required
def registrar_resultado(request):
    if request.method == 'POST':
        form = ResultadoSorteoForm(request.POST)
        if form.is_valid():
            resultado = form.save()
            
            # Marcar ganadores
            ventas_ganadoras = Venta.objects.filter(
                sorteo=resultado.sorteo,
                numero_sorteo_dia=resultado.numero_sorteo_dia,
                numero_apostado=resultado.numero_ganador,
                fecha_venta__date=resultado.fecha
            )
            ventas_ganadoras.update(es_ganador=True)
            
            return redirect('resultados_sorteo')
    else:
        form = ResultadoSorteoForm()
    
    resultados = ResultadoSorteo.objects.filter(fecha=timezone.now().date())
    return render(request, 'sistema/resultados.html', {
        'form': form,
        'resultados': resultados
    })

@login_required
def reporte_ganadores(request):
    fecha = request.GET.get('fecha', timezone.now().date())
    
    try:
        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
    except:
        fecha = timezone.now().date()
    
    resultados = ResultadoSorteo.objects.filter(fecha=fecha)
    ganadores = []
    
    for resultado in resultados:
        ventas_ganadoras = Venta.objects.filter(
            sorteo=resultado.sorteo,
            numero_sorteo_dia=resultado.numero_sorteo_dia,
            numero_apostado=resultado.numero_ganador,
            fecha_venta__date=fecha
        )
        
        if ventas_ganadoras.exists():
            for venta in ventas_ganadoras:
                ganadores.append({
                    'sorteo': resultado.sorteo,
                    'numero_sorteo': resultado.numero_sorteo_dia,
                    'cliente': venta.cliente,
                    'numero_ganador': resultado.numero_ganador,
                    'premio': venta.calcular_premio(),
                    'venta': venta
                })
        else:
            ganadores.append({
                'sorteo': resultado.sorteo,
                'numero_sorteo': resultado.numero_sorteo_dia,
                'cliente': 'Ganador desierto',
                'numero_ganador': resultado.numero_ganador,
                'premio': 0,
                'venta': None
            })
    
    return render(request, 'sistema/reporte_ganadores.html', {
        'ganadores': ganadores,
        'fecha_reporte': fecha
    })

@login_required
def reporte_recaudacion(request):
    fecha_inicio = request.GET.get('fecha_inicio', timezone.now().date() - timedelta(days=7))
    fecha_fin = request.GET.get('fecha_fin', timezone.now().date())
    sorteo_id = request.GET.get('sorteo', '')
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except:
        fecha_inicio = timezone.now().date() - timedelta(days=7)
        fecha_fin = timezone.now().date()
    
    ventas = Venta.objects.filter(fecha_venta__date__range=[fecha_inicio, fecha_fin])
    
    if sorteo_id:
        ventas = ventas.filter(sorteo_id=sorteo_id)
    
    total_recaudado = ventas.aggregate(Sum('monto'))['monto__sum'] or 0
    
    # Agrupar por sorteo
    recaudacion_por_sorteo = ventas.values('sorteo__nombre').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    )
    
    sorteos = Sorteo.objects.filter(activo=True)
    
    return render(request, 'sistema/reporte_recaudacion.html', {
        'recaudacion_por_sorteo': recaudacion_por_sorteo,
        'total_recaudado': total_recaudado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'sorteos': sorteos,
        'sorteo_seleccionado': sorteo_id
    })

@login_required
def voucher_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    return render(request, 'sistema/voucher.html', {'venta': venta})