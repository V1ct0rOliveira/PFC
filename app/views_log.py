from .models import logs

def registrar_log(acao, usuario, detalhes=""):
    """Função para registrar logs no banco de dados"""
    logs.objects.create(
        acao=acao,
        usuario=usuario.username if hasattr(usuario, 'username') else str(usuario),
        detalhes=detalhes
    )