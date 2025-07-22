# soldagem/models.py - VERSÃO CORRIGIDA E COMPLETA

from django.db import models
from django.utils import timezone
from decimal import Decimal
from core.models import Soldador, Usuario

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    numero = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    data_prevista = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    observacoes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"Pedido {self.numero}"

class Modulo(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['ordem_exibicao', 'nome']
    
    def __str__(self):
        return self.nome

class Componente(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    tempo_padrao = models.DecimalField(max_digits=10, decimal_places=2)  # em minutos
    considera_diametro = models.BooleanField(default=False)
    formula_calculo = models.TextField(blank=True, help_text="Fórmula para calcular tempo com diâmetro (use 'diametro' como variável)")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class Turno(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
    ]
    
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    data_turno = models.DateField()
    inicio_turno = models.DateTimeField()
    fim_turno = models.DateTimeField(null=True, blank=True)
    horas_disponiveis = models.DecimalField(max_digits=5, decimal_places=2, default=8)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    
    class Meta:
        ordering = ['-data_turno', '-inicio_turno']
        unique_together = ['soldador', 'data_turno']
    
    def __str__(self):
        return f"{self.soldador} - {self.data_turno}"

class Apontamento(models.Model):
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    numero_poste_tubo = models.CharField(max_length=100)
    diametro = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    inicio_processo = models.DateTimeField()
    fim_processo = models.DateTimeField(null=True, blank=True)
    tempo_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # em minutos
    tempo_padrao = models.DecimalField(max_digits=10, decimal_places=2)  # em minutos
    eficiencia_calculada = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # percentual
    data_criacao = models.DateTimeField(default=timezone.now)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-inicio_processo']
    
    def __str__(self):
        return f"{self.soldador} - {self.componente} - {self.inicio_processo}"
    
    def calcular_tempo_real(self):
        """Calcula o tempo real em minutos"""
        if self.fim_processo and self.inicio_processo:
            diff = self.fim_processo - self.inicio_processo
            self.tempo_real = Decimal(str(diff.total_seconds() / 60))
    
    def calcular_eficiencia(self):
        """Calcula a eficiência baseada no tempo padrão vs real"""
        if self.tempo_real and self.tempo_padrao and self.tempo_real > 0:
            self.eficiencia_calculada = (self.tempo_padrao / self.tempo_real) * 100
        else:
            self.eficiencia_calculada = Decimal('0')
    
    def save(self, *args, **kwargs):
        # Calcular automaticamente tempo real e eficiência se finalizado
        if self.fim_processo and self.inicio_processo:
            self.calcular_tempo_real()
            self.calcular_eficiencia()
        super().save(*args, **kwargs)

class TipoParada(models.Model):
    CATEGORIAS = [
        ('geral', 'Geral'),
        ('manutencao', 'Manutenção'),
        ('qualidade', 'Qualidade'),
    ]
    
    nome = models.CharField(max_length=150)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    penaliza_oee = models.BooleanField(default=True, help_text="Se False, ajusta horas disponíveis em vez de penalizar OEE")
    requer_senha_especial = models.BooleanField(default=False, help_text="Requer senha de qualidade ou manutenção")
    ativo = models.BooleanField(default=True)
    cor_exibicao = models.CharField(max_length=7, default='#dc3545', help_text="Cor em hexadecimal para exibição")
    
    class Meta:
        ordering = ['categoria', 'nome']
        verbose_name = 'Tipo de Parada'
        verbose_name_plural = 'Tipos de Paradas'
    
    def __str__(self):
        return f"{self.nome} ({self.get_categoria_display()})"

class Parada(models.Model):
    tipo_parada = models.ForeignKey(TipoParada, on_delete=models.CASCADE)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    apontamento = models.ForeignKey(Apontamento, on_delete=models.CASCADE, null=True, blank=True, help_text="Apontamento interrompido pela parada")
    inicio = models.DateTimeField()
    fim = models.DateTimeField(null=True, blank=True)
    duracao_minutos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    motivo_detalhado = models.TextField(blank=True, help_text="Descrição detalhada do motivo da parada")
    usuario_autorizacao = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, help_text="Usuário que autorizou a parada (qualidade/manutenção)")
    data_criacao = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-inicio']
        verbose_name = 'Parada'
        verbose_name_plural = 'Paradas'
    
    def __str__(self):
        return f"{self.soldador} - {self.tipo_parada} - {self.inicio}"
    
    def calcular_duracao(self):
        """Calcula a duração da parada em minutos"""
        if self.fim and self.inicio:
            diff = self.fim - self.inicio
            self.duracao_minutos = Decimal(str(diff.total_seconds() / 60))
    
    def save(self, *args, **kwargs):
        # Calcular automaticamente duração se finalizada
        if self.fim and self.inicio:
            self.calcular_duracao()
        super().save(*args, **kwargs)
    
    @property
    def duracao_formatada(self):
        """Retorna duração formatada em HH:MM"""
        if self.duracao_minutos:
            horas = int(self.duracao_minutos // 60)
            minutos = int(self.duracao_minutos % 60)
            return f"{horas:02d}:{minutos:02d}"
        return "00:00"
    
    @property
    def em_andamento(self):
        """Verifica se a parada está em andamento"""
        return self.fim is None