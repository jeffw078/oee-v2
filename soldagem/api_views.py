# Criar arquivo soldagem/api_views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class ApontamentoAPI(viewsets.ModelViewSet):
    """API REST para integração com sistemas externos"""
    queryset = Apontamento.objects.all()
    
    @action(detail=False, methods=['get'])
    def indicadores_dia(self, request):
        """Retorna indicadores OEE do dia"""
        data = request.query_params.get('data', timezone.now().date())
        oee = calcular_oee_periodo(data, data)
        return Response(oee)
    
    @action(detail=False, methods=['post'])
    def importar_pedidos(self, request):
        """Importa pedidos de sistema externo"""
        pedidos = request.data.get('pedidos', [])
        criados = 0
        
        for pedido_data in pedidos:
            pedido, created = Pedido.objects.get_or_create(
                numero=pedido_data['numero'],
                defaults={
                    'descricao': pedido_data.get('descricao', ''),
                    'data_prevista': pedido_data.get('data_prevista')
                }
            )
            if created:
                criados += 1
        
        return Response({'pedidos_criados': criados})