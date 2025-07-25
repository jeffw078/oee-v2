from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, Soldador, Modulo, Componente, Pedido, 
    Turno, Apontamento, TipoParada, Parada, LogAuditoria,
    ConfiguracaoSistema
)

# Primeiro, desregistrar o User padrão se existir
try:
    from django.contrib.auth.models import User
    admin.site.unregister(User)
except:
    pass

# Customizar admin site
admin.site.site_header = "Sistema OEE - Administração"
admin.site.site_title = "OEE Admin"
admin.site.index_title = "Gerenciamento do Sistema OEE"

# Admin personalizado para Usuario
class UsuarioAdmin(UserAdmin):
    """Admin personalizado para Usuario"""
    list_display = ('username', 'nome_completo', 'tipo_usuario', 'ativo', 'date_joined')
    list_filter = ('tipo_usuario', 'ativo', 'is_staff', 'is_superuser')
    search_fields = ('username', 'nome_completo', 'email')
    ordering = ('nome_completo',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações OEE', {
            'fields': ('nome_completo', 'tipo_usuario', 'ativo')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações OEE', {
            'fields': ('nome_completo', 'tipo_usuario', 'ativo')
        }),
    )

@admin.register(Soldador)
class SoldadorAdmin(admin.ModelAdmin):
    """Admin para Soldador"""
    list_display = ('get_nome_soldador', 'senha_simplificada', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'data_cadastro')
    search_fields = ('usuario__nome_completo', 'usuario__username')
    ordering = ('usuario__nome_completo',)
    
    def get_nome_soldador(self, obj):
        return obj.usuario.nome_completo
    get_nome_soldador.short_description = 'Nome do Soldador'

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    """Admin para Modulo"""
    list_display = ('nome', 'ordem_exibicao', 'ativo', 'data_criacao')
    list_filter = ('ativo', 'data_criacao')
    search_fields = ('nome', 'descricao')
    ordering = ('ordem_exibicao', 'nome')
    
    prepopulated_fields = {"descricao": ("nome",)}

@admin.register(Componente)
class ComponenteAdmin(admin.ModelAdmin):
    """Admin para Componente"""
    list_display = ('nome', 'tempo_padrao', 'considera_diametro', 'ativo', 'data_criacao')
    list_filter = ('considera_diametro', 'ativo', 'data_criacao')
    search_fields = ('nome', 'descricao')
    ordering = ('nome',)

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """Admin para Pedido"""
    list_display = ('numero', 'status', 'data_criacao', 'data_prevista')
    list_filter = ('status', 'data_criacao', 'data_prevista')
    search_fields = ('numero', 'descricao')
    ordering = ('-data_criacao',)
    
    readonly_fields = ('data_criacao',)

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    """Admin para Turno"""
    list_display = ('get_soldador_nome', 'data_turno', 'inicio_turno', 'fim_turno', 'status')
    list_filter = ('status', 'data_turno')
    search_fields = ('soldador__usuario__nome_completo',)
    ordering = ('-data_turno', '-inicio_turno')
    
    def get_soldador_nome(self, obj):
        return obj.soldador.usuario.nome_completo
    get_soldador_nome.short_description = 'Soldador'

@admin.register(Apontamento)
class ApontamentoAdmin(admin.ModelAdmin):
    """Admin para Apontamento"""
    list_display = ('get_soldador_nome', 'componente', 'modulo', 'get_pedido_numero', 'inicio_processo', 'fim_processo')
    list_filter = ('modulo', 'componente', 'data_criacao')
    search_fields = ('soldador__usuario__nome_completo', 'pedido__numero', 'numero_poste_tubo')
    ordering = ('-inicio_processo',)
    readonly_fields = ('tempo_real', 'eficiencia_calculada', 'data_criacao')
    
    def get_soldador_nome(self, obj):
        return obj.soldador.usuario.nome_completo
    get_soldador_nome.short_description = 'Soldador'
    
    def get_pedido_numero(self, obj):
        return obj.pedido.numero
    get_pedido_numero.short_description = 'Pedido'

@admin.register(TipoParada)
class TipoParadaAdmin(admin.ModelAdmin):
    """Admin para TipoParada"""
    list_display = ('nome', 'categoria', 'penaliza_oee', 'requer_senha_especial', 'ativo')
    list_filter = ('categoria', 'penaliza_oee', 'requer_senha_especial', 'ativo')
    search_fields = ('nome',)
    ordering = ('categoria', 'nome')

@admin.register(Parada)
class ParadaAdmin(admin.ModelAdmin):
    """Admin para Parada"""
    list_display = ('get_soldador_nome', 'tipo_parada', 'inicio', 'fim', 'duracao_minutos', 'get_categoria')
    list_filter = ('tipo_parada__categoria', 'data_criacao')
    search_fields = ('soldador__usuario__nome_completo', 'tipo_parada__nome')
    ordering = ('-inicio',)
    readonly_fields = ('duracao_minutos', 'data_criacao')
    
    def get_soldador_nome(self, obj):
        return obj.soldador.usuario.nome_completo
    get_soldador_nome.short_description = 'Soldador'
    
    def get_categoria(self, obj):
        return obj.tipo_parada.get_categoria_display()
    get_categoria.short_description = 'Categoria'

@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    """Admin para LogAuditoria"""
    list_display = ('get_usuario_nome', 'acao', 'tabela_afetada', 'timestamp')
    list_filter = ('acao', 'tabela_afetada', 'timestamp')
    search_fields = ('usuario__nome_completo', 'acao', 'tabela_afetada')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    def get_usuario_nome(self, obj):
        return obj.usuario.nome_completo if obj.usuario else 'Sistema'
    get_usuario_nome.short_description = 'Usuário'

@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    """Admin para ConfiguracaoSistema"""
    list_display = ('chave', 'valor', 'tipo_dado', 'data_atualizacao')
    list_filter = ('tipo_dado', 'data_atualizacao')
    search_fields = ('chave', 'descricao')
    ordering = ('chave',)

# Registrar Usuario apenas se não estiver registrado
try:
    admin.site.register(Usuario, UsuarioAdmin)
except admin.sites.AlreadyRegistered:
    # Se já estiver registrado, desregistrar e registrar novamente
    admin.site.unregister(Usuario)
    admin.site.register(Usuario, UsuarioAdmin)