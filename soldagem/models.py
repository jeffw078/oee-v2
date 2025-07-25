from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal
import json

class Usuario(AbstractUser):
    """Usuário base do sistema"""
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('analista', 'Analista'),
        ('qualidade', 'Qualidade'),
        ('manutencao', 'Manutenção'),
        ('soldador', 'Soldador'),
    ]
    
    nome_completo = models.CharField(max_length=150)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultimo_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.nome_completo} ({self.get_tipo_usuario_display()})"

class Soldador(models.Model):
    """Soldador com senha simplificada"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    senha_simplificada = models.CharField(max_length=10, help_text="Senha numérica para login rápido")
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Soldador"
        verbose_name_plural = "Soldadores"

    def __str__(self):
        return self.usuario.nome_completo

class Modulo(models.Model):
    """Módulos de soldagem"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.PositiveIntegerField(default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem_exibicao', 'nome']
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"

    def __str__(self):
        return self.nome

class Componente(models.Model):
    """Componentes que podem ser soldados"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    tempo_padrao = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tempo padrão em minutos")
    considera_diametro = models.BooleanField(default=False)
    formula_calculo = models.TextField(blank=True, help_text="Fórmula para cálculo baseado no diâmetro")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = "Componente"
        verbose_name_plural = "Componentes"

    def __str__(self):
        return self.nome

class Pedido(models.Model):
    """Pedidos de produção"""
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    numero = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_prevista = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['-data_criacao']
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return f"Pedido {self.numero}"

class Turno(models.Model):
    """Turnos de trabalho dos soldadores"""
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
    ]
    
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    data_turno = models.DateField()
    inicio_turno = models.DateTimeField()
    fim_turno = models.DateTimeField(null=True, blank=True)
    horas_disponiveis = models.DecimalField(max_digits=5, decimal_places=2, default=8.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')

    class Meta:
        unique_together = ['soldador', 'data_turno']
        ordering = ['-data_turno', '-inicio_turno']
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"

    def __str__(self):
        return f"{self.soldador.usuario.nome_completo} - {self.data_turno}"

class TipoParada(models.Model):
    """Tipos de paradas do sistema"""
    CATEGORIA_CHOICES = [
        ('geral', 'Geral'),
        ('manutencao', 'Manutenção'),
        ('qualidade', 'Qualidade'),
    ]
    
    nome = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    penaliza_oee = models.BooleanField(default=True, help_text="Se deve penalizar no cálculo do OEE")
    requer_senha_especial = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    cor_exibicao = models.CharField(max_length=7, default='#dc3545')

    class Meta:
        ordering = ['categoria', 'nome']
        verbose_name = "Tipo de Parada"
        verbose_name_plural = "Tipos de Parada"

    def __str__(self):
        return f"{self.nome} ({self.get_categoria_display()})"

class Apontamento(models.Model):
    """Apontamentos de soldagem"""
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    numero_poste_tubo = models.CharField(max_length=50)
    diametro = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    inicio_processo = models.DateTimeField()
    fim_processo = models.DateTimeField(null=True, blank=True)
    tempo_real = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Tempo real em minutos")
    tempo_padrao = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tempo padrão em minutos")
    eficiencia_calculada = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['-inicio_processo']
        verbose_name = "Apontamento"
        verbose_name_plural = "Apontamentos"

    def __str__(self):
        return f"{self.soldador.usuario.nome_completo} - {self.componente.nome} - {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Calcular tempo real e eficiência se processo finalizado
        if self.fim_processo and self.inicio_processo:
            delta = self.fim_processo - self.inicio_processo
            self.tempo_real = Decimal(str(delta.total_seconds() / 60))  # Em minutos
            
            if self.tempo_real and self.tempo_real > 0:
                self.eficiencia_calculada = self.tempo_padrao / self.tempo_real
        
        super().save(*args, **kwargs)

class Parada(models.Model):
    """Paradas durante o processo"""
    tipo_parada = models.ForeignKey(TipoParada, on_delete=models.CASCADE)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    apontamento = models.ForeignKey(Apontamento, on_delete=models.CASCADE, null=True, blank=True)
    inicio = models.DateTimeField()
    fim = models.DateTimeField(null=True, blank=True)
    duracao_minutos = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    motivo_detalhado = models.TextField(blank=True)
    usuario_autorizacao = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-inicio']
        verbose_name = "Parada"
        verbose_name_plural = "Paradas"

    def __str__(self):
        return f"{self.tipo_parada.nome} - {self.soldador.usuario.nome_completo}"

    def save(self, *args, **kwargs):
        # Calcular duração se finalizada
        if self.fim and self.inicio:
            delta = self.fim - self.inicio
            self.duracao_minutos = Decimal(str(delta.total_seconds() / 60))
        
        super().save(*args, **kwargs)

class LogAuditoria(models.Model):
    """Log de auditoria do sistema"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    acao = models.CharField(max_length=100)
    tabela_afetada = models.CharField(max_length=100)
    registro_id = models.PositiveIntegerField(null=True, blank=True)
    dados_antes = models.JSONField(null=True, blank=True)
    dados_depois = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"

    def __str__(self):
        return f"{self.acao} - {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"

class ConfiguracaoSistema(models.Model):
    """Configurações do sistema"""
    TIPO_DADOS_CHOICES = [
        ('string', 'Texto'),
        ('integer', 'Número Inteiro'),
        ('float', 'Número Decimal'),
        ('boolean', 'Verdadeiro/Falso'),
    ]
    
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField(blank=True)
    tipo_dado = models.CharField(max_length=20, choices=TIPO_DADOS_CHOICES, default='string')
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"

    def __str__(self):
        return f"{self.chave}: {self.valor}"

    def get_valor_tipado(self):
        """Retorna o valor convertido para o tipo correto"""
        if self.tipo_dado == 'integer':
            return int(self.valor)
        elif self.tipo_dado == 'float':
            return float(self.valor)
        elif self.tipo_dado == 'boolean':
            return self.valor.lower() in ['true', '1', 'sim', 'yes']
        return self.valor