from django.db import models
from soldagem.models import Usuario, Soldador, Apontamento
import math

class TipoDefeito(models.Model):
    """Tipos de defeitos de qualidade"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    cor_exibicao = models.CharField(max_length=7, default='#dc3545')
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de Defeito"
        verbose_name_plural = "Tipos de Defeito"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Defeito(models.Model):
    """Defeitos encontrados na qualidade"""
    tipo_defeito = models.ForeignKey(TipoDefeito, on_delete=models.CASCADE)
    apontamento = models.ForeignKey(Apontamento, on_delete=models.CASCADE)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    tamanho_mm = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        help_text="Tamanho do defeito em mm"
    )
    area_defeito = models.DecimalField(
        max_digits=12, 
        decimal_places=4, 
        null=True, 
        blank=True, 
        help_text="Área calculada em mm²"
    )
    data_deteccao = models.DateTimeField(auto_now_add=True)
    usuario_qualidade = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        limit_choices_to={'tipo_usuario': 'qualidade'}
    )
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Defeito"
        verbose_name_plural = "Defeitos"
        ordering = ['-data_deteccao']

    def __str__(self):
        return f"{self.tipo_defeito.nome} - {self.apontamento.componente.nome}"

    def save(self, *args, **kwargs):
        # Calcula área do defeito (assumindo defeito circular)
        if self.tamanho_mm:
            raio = float(self.tamanho_mm) / 2
            self.area_defeito = math.pi * (raio ** 2)
        super().save(*args, **kwargs)

class InspecaoQualidade(models.Model):
    """Inspeções de qualidade realizadas"""
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    usuario_qualidade = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        limit_choices_to={'tipo_usuario': 'qualidade'}
    )
    data_inspecao = models.DateTimeField(auto_now_add=True)
    periodo_inicio = models.DateTimeField()
    periodo_fim = models.DateTimeField()
    total_pecas_inspecionadas = models.PositiveIntegerField(default=0)
    total_defeitos_encontrados = models.PositiveIntegerField(default=0)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Inspeção de Qualidade"
        verbose_name_plural = "Inspeções de Qualidade"
        ordering = ['-data_inspecao']

    def __str__(self):
        return f"Inspeção {self.soldador.usuario.nome_completo} - {self.data_inspecao.strftime('%d/%m/%Y')}"

    @property
    def percentual_defeitos(self):
        """Calcula percentual de defeitos"""
        if self.total_pecas_inspecionadas > 0:
            return (self.total_defeitos_encontrados / self.total_pecas_inspecionadas) * 100
        return 0