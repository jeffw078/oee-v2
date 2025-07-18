from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from core.models import Usuario
from soldagem.models import Apontamento, Soldador

class TipoDefeito(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    cor_exibicao = models.CharField(max_length=7, default='#dc3545')
    
    class Meta:
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class Defeito(models.Model):
    tipo_defeito = models.ForeignKey(TipoDefeito, on_delete=models.CASCADE)
    apontamento = models.ForeignKey(Apontamento, on_delete=models.CASCADE)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    tamanho_mm = models.DecimalField(max_digits=8, decimal_places=2)
    area_defeito = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_deteccao = models.DateTimeField(default=timezone.now)
    usuario_qualidade = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data_deteccao']
    
    def __str__(self):
        return f"{self.tipo_defeito} - {self.soldador} - {self.data_deteccao}"
    
    def save(self, *args, **kwargs):
        # Calcular área do defeito (simplificado como círculo)
        if self.tamanho_mm:
            import math
            raio = float(self.tamanho_mm) / 2
            self.area_defeito = math.pi * (raio ** 2)
        super().save(*args, **kwargs)