import requests
from decouple import config
from django.utils import timezone

class WhatsAppService:
    """Serviço para envio de mensagens via WhatsApp usando UltraMsg API"""
    
    def __init__(self):
        self.instance_id = config('ULTRAMSG_INSTANCE_ID', default='')
        self.token = config('ULTRAMSG_TOKEN', default='')
        self.base_url = f"https://api.ultramsg.com/{self.instance_id}"
    
    def send_message(self, phone_number, message):
        """Envia mensagem de texto via WhatsApp"""
        if not self.instance_id or not self.token:
            return False
            
        url = f"{self.base_url}/messages/chat"
        
        payload = {
            'token': self.token,
            'to': phone_number,
            'body': message
        }
        
        try:
            response = requests.post(url, data=payload, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def send_notification(self, phone_number, tipo, dados):
        """Envia notificação formatada baseada no tipo"""
        if not phone_number:
            return False
            
        if tipo == 'nova_solicitacao':
            message = f"""🔔 *Nova Solicitação - Stock Flow*

            📋 *Solicitação #{dados['id']}*
            👤 *Solicitante:* {dados['solicitante']}
            📦 *Produto:* {dados['produto']}
            🏷️ *Código:* {dados['codigo']}
            📊 *Quantidade:* {dados['quantidade']} unidades
            📍 *Destino:* {dados['destino']}
            📅 *Data:* {dados['data']}

            ⏳ Status: *PENDENTE*

            Acesse o sistema para aprovar ou reprovar esta solicitação."""
        elif tipo == 'solicitacao_aprovada':
            message = f"""✅ *Solicitação Aprovada - Stock Flow*

            📋 *Solicitação #{dados['id']}*
            👤 *Solicitante:* {dados['solicitante']}
            👨💼 *Aprovador:* {dados['aprovador']}
            📦 *Produto:* {dados['produto']}
            📊 *Quantidade:* -{dados['quantidade']} unidades
            📍 *Destino:* {dados['destino']}
            📅 *Aprovação:* {dados['data_aprovacao']}

            ✅ Status: *APROVADA E RETIRADA*"""
        elif tipo == 'entrada_produto':
            message = f"""⬆️ *Entrada de Produto - Stock Flow*

            📦 *Produto:* {dados['produto']}
            🏷️ *Código:* {dados['codigo']}
            📊 *Quantidade:* +{dados['quantidade']} unidades
            👤 *Usuário:* {dados['usuario']}
            📅 *Data:* {dados['data']}

            ✅ Entrada registrada com sucesso!"""
        elif tipo == 'solicitacao_reprovada':
            message = f"""❌ *Solicitação Reprovada - Stock Flow*

            📋 *Solicitação #{dados['id']}*
            👤 *Solicitante:* {dados['solicitante']}
            👨💼 *Reprovador:* {dados['reprovador']}
            📦 *Produto:* {dados['produto']}
            📊 *Quantidade:* {dados['quantidade']} unidades
            📍 *Destino:* {dados['destino']}
            📅 *Reprovação:* {dados['data_reprovacao']}

            ❌ Status: *REPROVADA*"""
        else:
            message = ''
        
        if message:
            return self.send_message(phone_number, message)
        return False