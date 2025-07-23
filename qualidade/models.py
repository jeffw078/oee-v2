from django.db import models
import math

# Importar do app soldagem onde está o modelo Usuario
from soldagem.models import Usuario, Soldador, Apontamento

class TipoDefeito(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    cor_exibicao = models.CharField(max_length=7, default='#dc3545')

    class Meta:
        verbose_name = "Tipo de Defeito"
        verbose_name_plural = "Tipos de Defeito"

    def __str__(self):
        return self.nome

class Defeito(models.Model):
    tipo_defeito = models.ForeignKey(TipoDefeito, on_delete=models.CASCADE)
    apontamento = models.ForeignKey(Apontamento, on_delete=models.CASCADE)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    tamanho_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tamanho do defeito em mm")
    area_defeito = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="Área calculada em mm²")
    data_deteccao = models.DateTimeField(auto_now_add=True)
    usuario_qualidade = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['-data_deteccao']

    def __str__(self):
        return f"{self.tipo_defeito.nome} - {self.apontamento.componente.nome}"

    def save(self, *args, **kwargs):
        # Calcula área do defeito (assumindo defeito circular)
        if self.tamanho_mm:
            raio = float(self.tamanho_mm) / 2
            self.area_defeito = math.pi * (raio ** 2)
        super().save(*args, **kwargs)