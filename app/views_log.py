from .models import logs

def registrar_log(acao, usuario, detalhes=""):
    """Função para registrar logs no banco de dados"""
    
    # Se usuario for um objeto, pegar o username
    if hasattr(usuario, 'username'):
        username = usuario.username
    else:
        username = str(usuario)
    
    logs.objects.create(
        acao=acao,
        usuario=username,
        detalhes=detalhes
    )