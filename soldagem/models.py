from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal

class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('admin', 'Administrador'),
        ('analista', 'Analista'),
        ('qualidade', 'Qualidade'),
        ('manutencao', 'Manutenção'),
        ('soldador', 'Soldador'),
    ]
    
    nome_completo = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultimo_login = models.DateTimeField(null=True, blank=True)

    # Corrigir conflitos de relacionamento
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='soldagem_usuario_set',
        related_query_name='soldagem_usuario',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='soldagem_usuario_set',
        related_query_name='soldagem_usuario',
    )

    def __str__(self):
        return self.nome_completo

class Soldador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    senha_simplificada = models.CharField(max_length=10)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Soldador"
        verbose_name_plural = "Soldadores"

    def __str__(self):
        return self.usuario.nome_completo

class Modulo(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem_exibicao', 'nome']
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"

    def __str__(self):
        return self.nome

class Componente(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    tempo_padrao = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tempo padrão em minutos")
    considera_diametro = models.BooleanField(default=False)
    formula_calculo = models.TextField(blank=True, help_text="Fórmula para cálculo quando considera diâmetro")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Pedido(models.Model):
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

    def __str__(self):
        return self.numero

class Turno(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
    ]
    
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    data_turno = models.DateField()
    inicio_turno = models.DateTimeField()
    fim_turno = models.DateTimeField(null=True, blank=True)
    horas_disponiveis = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')

    class Meta:
        ordering = ['-data_turno', '-inicio_turno']
        unique_together = ['soldador', 'data_turno', 'status']

    def __str__(self):
        return f"{self.soldador} - {self.data_turno}"

class Apontamento(models.Model):
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    numero_poste_tubo = models.CharField(max_length=50)
    diametro = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    inicio_processo = models.DateTimeField()
    fim_processo = models.DateTimeField(null=True, blank=True)
    tempo_real = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    tempo_padrao = models.DecimalField(max_digits=8, decimal_places=2)
    eficiencia_calculada = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['-inicio_processo']

    def __str__(self):
        return f"{self.soldador} - {self.componente} - {self.inicio_processo.strftime('%d/%m/%Y %H:%M')}"

class TipoParada(models.Model):
    CATEGORIA_CHOICES = [
        ('geral', 'Geral'),
        ('manutencao', 'Manutenção'),
        ('qualidade', 'Qualidade'),
    ]
    
    nome = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    penaliza_oee = models.BooleanField(default=True)
    requer_senha_especial = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    cor_exibicao = models.CharField(max_length=7, default='#6c757d')

    class Meta:
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.get_categoria_display()})"

class Parada(models.Model):
    tipo_parada = models.ForeignKey(TipoParada, on_delete=models.CASCADE)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    apontamento = models.ForeignKey(Apontamento, on_delete=models.CASCADE, null=True, blank=True)
    inicio = models.DateTimeField()
    fim = models.DateTimeField(null=True, blank=True)
    duracao_minutos = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    motivo_detalhado = models.TextField(blank=True)
    usuario_autorizacao = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-inicio']

    def __str__(self):
        return f"{self.tipo_parada} - {self.soldador} - {self.inicio.strftime('%d/%m/%Y %H:%M')}"

class LogAuditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.CharField(max_length=100)
    tabela_afetada = models.CharField(max_length=50)
    registro_id = models.IntegerField()
    dados_antes = models.JSONField(null=True, blank=True)
    dados_depois = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.acao} - {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"