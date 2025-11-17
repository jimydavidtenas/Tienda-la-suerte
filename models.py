from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class Sorteo(models.Model):
    TIPOS_SORTEO = [
        ('LA_SANTA', 'La Santa'),
        ('LA_RIFA', 'La Rifa'),
        ('EL_SORTEO', 'El Sorteo'),
    ]
    
    nombre = models.CharField(max_length=50, choices=TIPOS_SORTEO)
    factor_pago = models.DecimalField(max_digits=10, decimal_places=2)
    sorteos_diarios = models.IntegerField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.get_nombre_display()

class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    sorteo = models.ForeignKey(Sorteo, on_delete=models.CASCADE)
    numero_apostado = models.IntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    atendido_por = models.ForeignKey(User, on_delete=models.CASCADE)
    numero_sorteo_dia = models.IntegerField()  # 1, 2, 3 para La Santa
    es_ganador = models.BooleanField(default=False)
    premio_pagado = models.BooleanField(default=False)
    fecha_pago_premio = models.DateTimeField(null=True, blank=True)

    def calcular_premio(self):
        premio = self.monto * self.sorteo.factor_pago
        
        # Verificar si es cumpleaños
        hoy = timezone.now().date()
        if self.cliente.fecha_nacimiento.month == hoy.month and self.cliente.fecha_nacimiento.day == hoy.day:
            premio *= 1.10  # 10% extra
        
        return premio

    def puede_reclamar_premio(self):
        if self.fecha_venta:
            fecha_limite = self.fecha_venta + timedelta(days=5)
            return timezone.now() <= fecha_limite
        return False

    def __str__(self):
        return f"{self.cliente} - {self.sorteo} - {self.numero_apostado:02d}"

class ResultadoSorteo(models.Model):
    sorteo = models.ForeignKey(Sorteo, on_delete=models.CASCADE)
    fecha = models.DateField()
    numero_ganador = models.IntegerField()
    numero_sorteo_dia = models.IntegerField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sorteo} - {self.fecha} - Sorteo {self.numero_sorteo_dia}"

class RecaudacionDiaria(models.Model):
    fecha = models.DateField()
    sorteo = models.ForeignKey(Sorteo, on_delete=models.CASCADE)
    total_recaudado = models.DecimalField(max_digits=15, decimal_places=2)
    total_premios = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ['fecha', 'sorteo']