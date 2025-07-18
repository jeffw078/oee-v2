from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Soldador, Modulo, Componente, LogAuditoria

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'nome_completo', 'tipo_usuario', 'ativo', 'last_login')
    list_filter = ('tipo_usuario', 'ativo', 'is_staff', 'is_superuser')
    search_fields = ('username', 'nome_completo', 'email')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('nome_completo', 'tipo_usuario', 'ativo')
        }),
    )

@admin.register(Soldador)
class SoldadorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'senha_simplificada', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'data_cadastro')
    search_fields = ('usuario__nome_completo', 'usuario__username')

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'ordem_exibicao', 'data_criacao')
    list_filter = ('ativo', 'data_criacao')
    search_fields = ('nome', 'descricao')
    list_editable = ('ativo', 'ordem_exibicao')

@admin.register(Componente)
class ComponenteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tempo_padrao', 'considera_diametro', 'ativo', 'data_criacao')
    list_filter = ('considera_diametro', 'ativo', 'data_criacao')
    search_fields = ('nome', 'descricao')
    list_editable = ('ativo',)

@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'acao', 'tabela_afetada', 'timestamp')
    list_filter = ('acao', 'tabela_afetada', 'timestamp')
    search_fields = ('usuario__nome_completo', 'acao', 'tabela_afetada')
    readonly_fields = ('usuario', 'acao', 'tabela_afetada', 'registro_id', 
                      'dados_antes', 'dados_depois', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        return False  # Não permitir adicionar logs manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Não permitir editar logs
