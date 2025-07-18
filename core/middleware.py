import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import LogAuditoria

logger = logging.getLogger('audit')

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Salvar dados originais para comparação
        if request.method in ['POST', 'PUT', 'DELETE']:
            request._audit_data = {
                'timestamp': timezone.now(),
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'method': request.method,
                'path': request.path,
                'user': request.user if request.user.is_authenticated else None
            }
    
    def process_response(self, request, response):
        # Log de auditoria para operações importantes
        if hasattr(request, '_audit_data') and response.status_code < 400:
            audit_data = request._audit_data
            
            # Criar log de auditoria
            try:
                if audit_data['user']:
                    LogAuditoria.objects.create(
                        usuario=audit_data['user'],
                        acao=f"{audit_data['method']} {audit_data['path']}",
                        tabela_afetada='Sistema',
                        registro_id='0',
                        ip_address=audit_data['ip_address'],
                        user_agent=audit_data['user_agent'],
                        timestamp=audit_data['timestamp']
                    )
                
                # Log em arquivo
                logger.info(f"AUDIT: {audit_data['user']} | {audit_data['method']} {audit_data['path']} | {audit_data['ip_address']}")
                
            except Exception as e:
                logger.error(f"Erro no log de auditoria: {e}")
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip