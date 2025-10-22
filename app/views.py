# Importações necessárias do Django e outras bibliotecas
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout  
from django.contrib.auth.decorators import login_required  
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from decouple import config
import re
from .models import CustomUser, Product, Solicitacao, Movimentacao, Saidas, Entradas

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def validar_senha_forte(senha):
    """Valida se a senha atende aos critérios de segurança"""
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres"
    
    if not re.search(r'[A-Z]', senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', senha):
        return False, "A senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'\d', senha):
        return False, "A senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False, "A senha deve conter pelo menos um caractere especial (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Senha válida"

# ============================================================================
# VIEWS GERAIS
# ============================================================================

def home(request):
    """View da página inicial do sistema"""
    if request.user.is_authenticated:
        auth_logout(request)
    return render(request, 'home.html')

# ============================================================================
# VIEWS DE AUTENTICAÇÃO E USUÁRIO
# ============================================================================

def cadastro(request):
    """View para cadastro de novos usuários"""
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        nome = request.POST['nome']
        sobrenome = request.POST['sobrenome']
        telefone = request.POST['telefone']
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Usuário já existe')
            return render(request, 'cadastro.html')
        
        senha_valida, mensagem = validar_senha_forte(password)
        if not senha_valida:
            messages.error(request, mensagem)
            return render(request, 'cadastro.html')
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            nome=nome,
            sobrenome=sobrenome,
            telefone=telefone,
            nivel_acesso='comum'
        )
        
        messages.success(request, 'Cadastro realizado com sucesso!')
        return redirect('login')
    
    return render(request, 'cadastro.html')

def login(request):
    """View para autenticação de usuários"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.totp_enabled:
                request.session['setup_user_id'] = user.id
                return redirect('setup_totp')
            else:
                request.session['login_user_id'] = user.id
                return redirect('verify_totp')
        else:
            messages.error(request, 'Credenciais inválidas')
    
    return render(request, 'login.html')

def logout(request):
    """View para logout do usuário"""
    auth_logout(request)
    return redirect('home')

@login_required
def perfil(request):
    if request.method == 'POST':
        user = request.user
        user.nome = request.POST.get('nome', user.nome)
        user.sobrenome = request.POST.get('sobrenome', user.sobrenome)
        user.email = request.POST.get('email', user.email)
        user.telefone = request.POST.get('telefone', user.telefone)
        
        nova_senha = request.POST.get('nova_senha')
        if nova_senha:
            senha_valida, mensagem = validar_senha_forte(nova_senha)
            if not senha_valida:
                messages.error(request, mensagem)
                return render(request, 'perfil.html')
            user.set_password(nova_senha)
        
        user.save()
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('perfil')
    
    return render(request, 'perfil.html')

def tabela_usuarios(request):
    """View para exibir tabela de usuários - BLOQUEADA para usuário comum"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    usuarios = CustomUser.objects.all().order_by('username')
    return render(request, 'tabela_usuarios.html', {'usuarios': usuarios})

# ============================================================================
# VIEWS DE RECUPERAÇÃO DE SENHA
# ============================================================================

def esqueci_senha(request):
    """View para solicitar reset de senha"""
    if request.method == 'POST':
        email = request.POST['email']
        
        try:
            user = CustomUser.objects.get(email=email)
            
            import random
            token = str(random.randint(100000, 999999))
            
            request.session['reset_token'] = token
            request.session['reset_user_id'] = user.id
            request.session['token_expires'] = (timezone.now() + timezone.timedelta(minutes=15)).timestamp()
            
            from django.core.mail import send_mail
            
            send_mail(
                'Token de Reset - Sistema de Estoque',
                f'Seu token para redefinir a senha é: {token}\n\nEste token expira em 15 minutos.',
                config('DEFAULT_FROM_EMAIL', default='noreply@sistema.com'),
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Token enviado para seu email!')
            return redirect('verificar_token')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'Email não encontrado')
    
    return render(request, 'esqueci_senha.html')

def verificar_token(request):
    """View para verificar token enviado por email"""
    if 'reset_token' not in request.session:
        messages.error(request, 'Sessão expirada. Solicite um novo token.')
        return redirect('esqueci_senha')
    
    if timezone.now().timestamp() > request.session.get('token_expires', 0):
        del request.session['reset_token']
        del request.session['reset_user_id']
        del request.session['token_expires']
        messages.error(request, 'Token expirado. Solicite um novo token.')
        return redirect('esqueci_senha')
    
    if request.method == 'POST':
        token_digitado = request.POST['token']
        
        if token_digitado == request.session['reset_token']:
            return redirect('nova_senha')
        else:
            messages.error(request, 'Token inválido')
    
    return render(request, 'verificar_token.html')

def nova_senha(request):
    """View para definir nova senha após verificar token"""
    if 'reset_token' not in request.session or 'reset_user_id' not in request.session:
        messages.error(request, 'Sessão inválida. Inicie o processo novamente.')
        return redirect('esqueci_senha')
    
    if request.method == 'POST':
        nova_senha = request.POST['nova_senha']
        confirmar_senha = request.POST['confirmar_senha']
        
        if nova_senha != confirmar_senha:
            messages.error(request, 'Senhas não coincidem')
            return render(request, 'nova_senha.html')
        
        senha_valida, mensagem = validar_senha_forte(nova_senha)
        if not senha_valida:
            messages.error(request, mensagem)
            return render(request, 'nova_senha.html')
        
        user = CustomUser.objects.get(id=request.session['reset_user_id'])
        user.set_password(nova_senha)
        user.save()
        
        del request.session['reset_token']
        del request.session['reset_user_id']
        del request.session['token_expires']
        
        messages.success(request, 'Senha alterada com sucesso!')
        return redirect('login')
    
    return render(request, 'nova_senha.html')

# ============================================================================
# VIEWS DE AUTENTICAÇÃO 2FA
# ============================================================================

def setup_totp(request):
    """Configuração inicial do TOTP"""
    if 'setup_user_id' not in request.session:
        return redirect('login')
    
    user = CustomUser.objects.get(id=request.session['setup_user_id'])
    
    if request.method == 'POST':
        import pyotp
        token = request.POST['token']
        
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(token):
            user.totp_enabled = True
            user.save()
            auth_login(request, user)
            del request.session['setup_user_id']
            messages.success(request, 'Autenticação 2FA configurada com sucesso!')
            if user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            elif user.nivel_acesso == 'superadmin':
                return redirect('dashboard_super')
        else:
            messages.error(request, 'Código inválido')
    
    if not user.totp_secret:
        import pyotp
        user.totp_secret = pyotp.random_base32()
        user.save()
    
    import pyotp
    import qrcode
    from io import BytesIO
    import base64
    
    totp = pyotp.TOTP(user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.username,
        issuer_name="Stock Flow"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'setup_totp.html', {
        'qr_code': qr_code,
        'secret': user.totp_secret
    })

def verify_totp(request):
    """Verificação do TOTP no login"""
    if 'login_user_id' not in request.session:
        return redirect('login')
    
    user = CustomUser.objects.get(id=request.session['login_user_id'])
    
    if request.method == 'POST':
        import pyotp
        token = request.POST['token']
        
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(token):
            auth_login(request, user)
            del request.session['login_user_id']
            
            if user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            elif user.nivel_acesso == 'superadmin':
                return redirect('dashboard_super')
        else:
            messages.error(request, 'Código inválido')
    
    return render(request, 'verify_totp.html')

@login_required
def reset_user_totp(request, user_id):
    """Reset TOTP de outro usuário (apenas superadmin)"""
    if request.user.nivel_acesso != 'superadmin':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_super')
    
    user = get_object_or_404(CustomUser, id=user_id)
    user.totp_secret = None
    user.totp_enabled = False
    user.save()
    
    messages.success(request, f'Autenticação 2FA resetada para {user.username}')
    return redirect('dashboard_super')

# ============================================================================
# VIEWS DE DASHBOARD
# ============================================================================

@login_required
def dashboard(request):
    """Redireciona para dashboard específico baseado no nível de acesso"""
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    elif request.user.nivel_acesso == 'superadmin':
        return redirect('dashboard_super')

@login_required
def dashboard_comum(request):
    """Dashboard para usuários comuns"""
    produtos = Product.objects.all()
    minhas_solicitacoes = Solicitacao.objects.filter(solicitante=request.user).order_by('-data_solicitacao')[:10]
    
    context = {
        'produtos': produtos,
        'minhas_solicitacoes': minhas_solicitacoes,
    }
    return render(request, 'dashboard_comum.html', context)

@login_required
def dashboard_admin(request):
    """Dashboard para administradores"""
    if request.user.nivel_acesso not in ['admin', 'superadmin']:
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    produtos = Product.objects.all()
    solicitacoes_pendentes = Solicitacao.objects.filter(status='PENDENTE').order_by('-data_solicitacao')
    entradas_recentes = Entradas.objects.select_related('produto', 'usuario').order_by('-data_entrada')[:50]
    saidas_recentes = Saidas.objects.select_related('produto', 'usuario').order_by('-data_saida')[:50]
    
    context = {
        'produtos': produtos,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'entradas_recentes': entradas_recentes,
        'saidas_recentes': saidas_recentes,
    }
    return render(request, 'dashboard_admin.html', context)

@login_required
def dashboard_super(request):
    """Dashboard para superadministradores"""
    if request.user.nivel_acesso != 'superadmin':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    produtos = Product.objects.all()
    solicitacoes_pendentes = Solicitacao.objects.filter(status='PENDENTE').order_by('-data_solicitacao')
    entradas_recentes = Entradas.objects.select_related('produto', 'usuario').order_by('-data_entrada')[:50]
    saidas_recentes = Saidas.objects.select_related('produto', 'usuario').order_by('-data_saida')[:50]
    usuarios = CustomUser.objects.all()
    
    context = {
        'produtos': produtos,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'entradas_recentes': entradas_recentes,
        'saidas_recentes': saidas_recentes,
        'usuarios': usuarios,
    }
    return render(request, 'dashboard_super.html', context)

# ============================================================================
# VIEWS DE ESTOQUE - PRODUTOS
# ============================================================================

@login_required
def cadastro_produto(request):
    """View para cadastro de novos produtos no estoque - BLOQUEADA para usuário comum"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    if request.method == 'POST':
        nome = request.POST['nome']
        quantidade = int(request.POST['quantidade'])
        local = request.POST['local']
        codigo = request.POST['codigo']
        carencia = request.POST.get('carencia') == 'on'
        
        if Product.objects.filter(codigo=codigo).exists():
            messages.error(request, 'Código do produto já existe')
            return render(request, 'cadastro_produto.html')
        
        Product.objects.create(
            nome=nome,
            quantidade=quantidade,
            local=local,
            codigo=codigo,
            carencia=carencia
        )
        
        messages.success(request, 'Produto cadastrado com sucesso!')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    return render(request, 'cadastro_produto.html')

@login_required
def estoque_geral(request):
    """View para exibir o estoque geral de produtos"""
    produtos = Product.objects.all()
    return render(request, 'estoque_geral.html', {'produtos': produtos})

# ============================================================================
# VIEWS DE ESTOQUE - MOVIMENTAÇÕES
# ============================================================================

@login_required
def listar_movimentacoes(request):
    """View para listar movimentações com filtros - BLOQUEADA para usuário comum"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    movimentacoes = Movimentacao.objects.select_related('produto', 'usuario').order_by('-data_hora')
    
    codigo = request.GET.get('codigo')
    nome = request.GET.get('nome')
    tipo = request.GET.get('tipo')
    usuario_id = request.GET.get('usuario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if codigo:
        movimentacoes = movimentacoes.filter(produto__codigo__icontains=codigo)
    if nome:
        movimentacoes = movimentacoes.filter(produto__nome__icontains=nome)
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    if usuario_id:
        movimentacoes = movimentacoes.filter(usuario_id=usuario_id)
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_hora__date__gte=data_inicio)
    if data_fim:
        movimentacoes = movimentacoes.filter(data_hora__date__lte=data_fim)
    
    usuarios = CustomUser.objects.all()
    tipos = Movimentacao.TIPO_CHOICES
    
    context = {
        'movimentacoes': movimentacoes[:100],
        'usuarios': usuarios,
        'tipos': tipos,
        'filtros': {
            'codigo': codigo,
            'nome': nome,
            'tipo': tipo,
            'usuario_id': usuario_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    
    return render(request, 'movimentacoes.html', context)

# ============================================================================
# VIEWS DE ESTOQUE - SOLICITAÇÕES
# ============================================================================

@login_required
def solicitar_produto(request):
    """View para solicitar produtos"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        quantidade = int(request.POST.get('quantidade', 0))
        destino = request.POST.get('destino', '').strip()
        
        if quantidade <= 0:
            messages.error(request, 'Quantidade deve ser maior que zero')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        if not destino:
            messages.error(request, 'Campo destino é obrigatório')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        try:
            produto = Product.objects.get(codigo=codigo)
        except Product.DoesNotExist:
            messages.error(request, 'Produto não encontrado')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        solicitacao = Solicitacao.objects.create(
            produto=produto,
            quantidade=quantidade,
            destino=destino,
            solicitante=request.user
        )
        
        Movimentacao.objects.create(
            tipo='SOLICITACAO',
            produto=produto,
            quantidade=quantidade,
            usuario=request.user,
            referencia_id=solicitacao.id,
            observacao=f'Solicitação #{solicitacao.id} criada - Destino: {destino}'
        )
        
        messages.success(request, f'Solicitação #{solicitacao.id} criada com sucesso!')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

@login_required
def aprovar_solicitacao(request, solicitacao_id):
    """View para aprovar solicitação e executar retirada automaticamente"""
    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id, status='PENDENTE')
    produto = solicitacao.produto
    
    if produto.quantidade < solicitacao.quantidade:
        messages.error(request, f'Estoque insuficiente para aprovação. Disponível: {produto.quantidade}, Solicitado: {solicitacao.quantidade}')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    with transaction.atomic():
        solicitacao.status = 'ATENDIDA'
        solicitacao.aprovador = request.user
        solicitacao.data_aprovacao = timezone.now()
        solicitacao.save()
        
        produto.quantidade -= solicitacao.quantidade
        produto.save()
        
        Saidas.objects.create(
            produto=produto,
            quantidade=solicitacao.quantidade,
            destino=solicitacao.destino,
            usuario=request.user
        )
        
        Movimentacao.objects.create(
            tipo='RETIRADA',
            produto=produto,
            quantidade=solicitacao.quantidade,
            usuario=request.user,
            referencia_id=solicitacao.id,
            observacao=f'Solicitação #{solicitacao.id} aprovada e retirada executada automaticamente - Destino: {solicitacao.destino}'
        )
    
    messages.success(request, f'Solicitação #{solicitacao.id} aprovada e retirada executada automaticamente!')
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

@login_required
def reprovar_solicitacao(request, solicitacao_id):
    """View para reprovar solicitação"""
    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id, status='PENDENTE')
    
    solicitacao.status = 'REPROVADA'
    solicitacao.aprovador = request.user
    solicitacao.data_aprovacao = timezone.now()
    solicitacao.save()
    
    messages.success(request, f'Solicitação #{solicitacao.id} reprovada!')
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

# ============================================================================
# VIEWS DE ESTOQUE - ENTRADAS E SAÍDAS
# ============================================================================

@login_required
def entrada_produto(request):
    """View para entrada de produtos"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        quantidade = int(request.POST.get('quantidade', 0))
        
        if quantidade <= 0:
            messages.error(request, 'Quantidade deve ser maior que zero')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        try:
            produto = Product.objects.get(codigo=codigo)
        except Product.DoesNotExist:
            messages.error(request, 'Produto não encontrado')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        with transaction.atomic():
            produto.quantidade += quantidade
            produto.save()
            
            Movimentacao.objects.create(
                tipo='ENTRADA',
                produto=produto,
                quantidade=quantidade,
                usuario=request.user,
                observacao=f'Entrada de {quantidade} unidades'
            )

            Entradas.objects.create(
                produto=produto,
                quantidade=quantidade,
                usuario=request.user,
            )
        
        messages.success(request, f'Entrada de {quantidade} unidades de {produto.nome} registrada!')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

@login_required
def retirada_direta(request):
    """View para retirada direta de produtos (sem solicitação)"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        quantidade = int(request.POST.get('quantidade', 0))
        destino = request.POST.get('destino', '').strip()
        
        if quantidade <= 0:
            messages.error(request, 'Quantidade deve ser maior que zero')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        if not destino:
            messages.error(request, 'Campo destino é obrigatório')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        try:
            produto = Product.objects.get(codigo=codigo)
        except Product.DoesNotExist:
            messages.error(request, 'Produto não encontrado')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        if produto.quantidade < quantidade:
            messages.error(request, f'Estoque insuficiente. Disponível: {produto.quantidade}, Solicitado: {quantidade}')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        with transaction.atomic():
            produto.quantidade -= quantidade
            produto.save()
            
            Saidas.objects.create(
                produto=produto,
                quantidade=quantidade,
                destino=destino,
                usuario=request.user
            )
            
            Movimentacao.objects.create(
                tipo='RETIRADA',
                produto=produto,
                quantidade=quantidade,
                usuario=request.user,
                observacao=f'Retirada direta de {quantidade} unidades - Destino: {destino}'
            )
        
        messages.success(request, f'Retirada de {quantidade} unidades de {produto.nome} realizada com sucesso!')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

# ============================================================================
# VIEWS DE RELATÓRIOS
# ============================================================================

@login_required
def gerar_relatorio_pdf(request):
    """View para gerar relatório PDF do estoque - BLOQUEADA para usuário comum"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from datetime import datetime
    
    produtos = Product.objects.all().order_by('nome')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph("Relatório de Estoque Geral", styles['Title'])
    elements.append(title)
    
    date = Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
    elements.append(date)
    elements.append(Paragraph("<br/>", styles['Normal']))
    
    data = [['Código', 'Nome', 'Quantidade', 'Local']]
    
    for produto in produtos:
        data.append([
            produto.codigo,
            produto.nome,
            str(produto.quantidade),
            produto.local,
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    return response