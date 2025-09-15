# Importações necessárias do Django
from django.shortcuts import render, redirect, get_object_or_404  # Para renderizar templates e redirecionar
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout  # Sistema de autenticação
from django.contrib.auth.decorators import login_required  # Decorator para proteger views
from django.contrib import messages  # Sistema de mensagens para feedback ao usuário
from django.http import HttpResponseForbidden
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from .models import CustomUser, Product, Solicitacao, Movimentacao, Saidas, Entradas  # Modelos personalizados da aplicação

def home(request):
    """View da página inicial do sistema"""
    # Força logout para garantir que os botões aparecem
    if request.user.is_authenticated:
        auth_logout(request)
    return render(request, 'home.html')

def cadastro(request):
    """View para cadastro de novos usuários"""
    if request.method == 'POST':
        # Captura os dados do formulário
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        nome = request.POST['nome']
        sobrenome = request.POST['sobrenome']
        telefone = request.POST['telefone']
        
        # Verifica se o usuário já existe
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Usuário já existe')
            return render(request, 'cadastro.html')
        
        # Cria novo usuário com nível de acesso padrão 'comum'
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            nome=nome,
            sobrenome=sobrenome,
            telefone=telefone,
            nivel_acesso='comum'
        )
        
        # Mensagem de sucesso e redirecionamento para login
        messages.success(request, 'Cadastro realizado com sucesso!')
        return redirect('login')
    
    # Se não for POST, renderiza o formulário de cadastro
    return render(request, 'cadastro.html')

def login(request):
    """View para autenticação de usuários"""
    if request.method == 'POST':
        # Captura credenciais do formulário
        username = request.POST['username']
        password = request.POST['password']
        
        # Autentica o usuário
        user = authenticate(request, username=username, password=password)
        if user:
            # Login direto sem 2FA
            auth_login(request, user)
            return redirect('dashboard')
        else:
            # Credenciais inválidas, exibe mensagem de erro
            messages.error(request, 'Credenciais inválidas')
    
    # Renderiza formulário de login
    return render(request, 'login.html')

@login_required  # Decorator que exige login para acessar esta view
def dashboard(request):
    """View do painel principal do sistema (protegida por login)"""
    # Dados para o dashboard
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
    
    return render(request, 'dashboard.html', context)

def verify_2fa(request):
    """View para verificação 2FA"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = CustomUser.objects.get(id=request.session['user_id'])
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_code':
            messages.success(request, 'Código enviado para seu telefone!')
            return render(request, 'verify_2fa.html', {'code_sent': True})
        
        elif action == 'verify_code':
            code = request.POST['code']
            # Simulação de verificação (aceita qualquer código)
            auth_login(request, user)
            user.is_verified = True
            user.save()
            del request.session['user_id']
            messages.success(request, 'Login realizado com sucesso!')
            return redirect('dashboard')
    
    return render(request, 'verify_2fa.html')

def logout(request):
    """View para logout do usuário"""
    auth_logout(request)  # Encerra a sessão do usuário
    return redirect('home')  # Redireciona para página inicial

@login_required
def listar_movimentacoes(request):
    """View para listar movimentações com filtros"""
    movimentacoes = Movimentacao.objects.select_related('produto', 'usuario').order_by('-data_hora')
    
    # Filtros
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
        'movimentacoes': movimentacoes[:100],  # Limitar a 100 registros
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

@login_required
def perfil(request):
    """View para configurações do usuário"""
    if request.method == 'POST':
        # Atualizar dados do usuário
        user = request.user
        user.nome = request.POST.get('nome', user.nome)
        user.sobrenome = request.POST.get('sobrenome', user.sobrenome)
        user.email = request.POST.get('email', user.email)
        user.telefone = request.POST.get('telefone', user.telefone)
        
        # Alterar senha se fornecida
        nova_senha = request.POST.get('nova_senha')
        if nova_senha:
            user.set_password(nova_senha)
        
        user.save()
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('perfil')
    
    return render(request, 'perfil.html')

@login_required  # Protege a view, apenas usuários logados podem cadastrar produtos
def cadastro_produto(request):
    """View para cadastro de novos produtos no estoque"""
    if request.method == 'POST':
        # Captura dados do formulário de produto
        nome = request.POST['nome']
        quantidade = int(request.POST['quantidade'])  # Converte para inteiro
        local = request.POST['local']
        codigo = request.POST['codigo']
        carencia = request.POST.get('carencia') == 'on'  # Converte checkbox para boolean
        
        # Verifica se já existe produto com o mesmo código (código deve ser único)
        if Product.objects.filter(codigo=codigo).exists():
            messages.error(request, 'Código do produto já existe')
            return render(request, 'cadastro_produto.html')
        
        # Cria novo produto no banco de dados
        Product.objects.create(
            nome=nome,
            quantidade=quantidade,
            local=local,
            codigo=codigo,
            carencia=carencia
        )
        
        # Mensagem de sucesso e redirecionamento para dashboard
        messages.success(request, 'Produto cadastrado com sucesso!')
        return redirect('dashboard')
    
    # Se não for POST, renderiza formulário de cadastro de produto
    return render(request, 'cadastro_produto.html')

@login_required  # Protege a view, apenas usuários logados podem ver o estoque
def estoque_geral(request):
    """View para exibir o estoque geral de produtos"""
    # Recupera todos os produtos do banco de dados
    produtos = Product.objects.all()

    # Renderiza template com os produtos
    return render(request, 'estoque_geral.html', {'produtos': produtos})

@login_required
def gerar_relatorio_pdf(request):
    """View para gerar relatório PDF do estoque"""
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from datetime import datetime
    
    # Busca todos os produtos
    produtos = Product.objects.all().order_by('nome')
    
    # Cria resposta HTTP para PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # Cria documento PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph("Relatório de Estoque Geral", styles['Title'])
    elements.append(title)
    
    # Data
    date = Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
    elements.append(date)
    elements.append(Paragraph("<br/>", styles['Normal']))
    
    # Dados da tabela
    data = [['Código', 'Nome', 'Quantidade', 'Local']]
    
    for produto in produtos:
        data.append([
            produto.codigo,
            produto.nome,
            str(produto.quantidade),
            produto.local,
        ])
    
    # Cria tabela
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
    
    # Gera PDF
    doc.build(elements)
    return response

@login_required
def solicitar_produto(request):
    """View para solicitar produtos"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        quantidade = int(request.POST.get('quantidade', 0))
        destino = request.POST.get('destino', '').strip()
        
        if quantidade <= 0:
            messages.error(request, 'Quantidade deve ser maior que zero')
            return redirect('dashboard')
        
        if not destino:
            messages.error(request, 'Campo destino é obrigatório')
            return redirect('dashboard')
        
        try:
            produto = Product.objects.get(codigo=codigo)
        except Product.DoesNotExist:
            messages.error(request, 'Produto não encontrado')
            return redirect('dashboard')
        
        # Criar solicitação
        solicitacao = Solicitacao.objects.create(
            produto=produto,
            quantidade=quantidade,
            destino=destino,
            solicitante=request.user
        )
        
        # Registrar movimentação
        Movimentacao.objects.create(
            tipo='SOLICITACAO',
            produto=produto,
            quantidade=quantidade,
            usuario=request.user,
            referencia_id=solicitacao.id,
            observacao=f'Solicitação #{solicitacao.id} criada - Destino: {destino}'
        )
        
        messages.success(request, f'Solicitação #{solicitacao.id} criada com sucesso!')
        return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def aprovar_solicitacao(request, solicitacao_id):
    """View para aprovar solicitação e executar retirada automaticamente"""
    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id, status='PENDENTE')
    produto = solicitacao.produto
    
    # Verificar se há estoque suficiente
    if produto.quantidade < solicitacao.quantidade:
        messages.error(request, f'Estoque insuficiente para aprovação. Disponível: {produto.quantidade}, Solicitado: {solicitacao.quantidade}')
        return redirect('dashboard')
    
    with transaction.atomic():
        # Aprovar solicitação
        solicitacao.status = 'ATENDIDA'  # Já marca como atendida
        solicitacao.aprovador = request.user
        solicitacao.data_aprovacao = timezone.now()
        solicitacao.save()
        
        # Executar retirada automaticamente
        produto.quantidade -= solicitacao.quantidade
        produto.save()
        
        # Criar registro de saída
        Saidas.objects.create(
            produto=produto,
            quantidade=solicitacao.quantidade,
            destino=solicitacao.destino,
            usuario=request.user
        )
        
        # Registrar movimentação
        Movimentacao.objects.create(
            tipo='RETIRADA',
            produto=produto,
            quantidade=solicitacao.quantidade,
            usuario=request.user,
            referencia_id=solicitacao.id,
            observacao=f'Solicitação #{solicitacao.id} aprovada e retirada executada automaticamente - Destino: {solicitacao.destino}'
        )
    
    messages.success(request, f'Solicitação #{solicitacao.id} aprovada e retirada executada automaticamente!')
    return redirect('dashboard')

@login_required
def reprovar_solicitacao(request, solicitacao_id):
    """View para reprovar solicitação"""
    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id, status='PENDENTE')
    
    solicitacao.status = 'REPROVADA'
    solicitacao.aprovador = request.user
    solicitacao.data_aprovacao = timezone.now()
    solicitacao.save()
    
    messages.success(request, f'Solicitação #{solicitacao.id} reprovada!')
    return redirect('dashboard')

@login_required
def entrada_produto(request):
    """View para entrada de produtos"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        quantidade = int(request.POST.get('quantidade', 0))
        
        if quantidade <= 0:
            messages.error(request, 'Quantidade deve ser maior que zero')
            return redirect('dashboard')
        
        try:
            produto = Product.objects.get(codigo=codigo)
        except Product.DoesNotExist:
            messages.error(request, 'Produto não encontrado')
            return redirect('dashboard')
        
        with transaction.atomic():
            # Atualizar estoque
            produto.quantidade += quantidade
            produto.save()
            
            # Registrar na tabela movimentação
            Movimentacao.objects.create(
                tipo='ENTRADA',
                produto=produto,
                quantidade=quantidade,
                usuario=request.user,
                observacao=f'Entrada de {quantidade} unidades'
            )

            # Criar registro de entrada
            Entradas.objects.create(
                produto=produto,
                quantidade=quantidade,
                usuario=request.user,
            )
        
        messages.success(request, f'Entrada de {quantidade} unidades de {produto.nome} registrada!')
        return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def retirada_direta(request):
    """View para retirada direta de produtos (sem solicitação)"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        quantidade = int(request.POST.get('quantidade', 0))
        destino = request.POST.get('destino', '').strip()
        
        if quantidade <= 0:
            messages.error(request, 'Quantidade deve ser maior que zero')
            return redirect('dashboard')
        
        if not destino:
            messages.error(request, 'Campo destino é obrigatório')
            return redirect('dashboard')
        
        try:
            produto = Product.objects.get(codigo=codigo)
        except Product.DoesNotExist:
            messages.error(request, 'Produto não encontrado')
            return redirect('dashboard')
        
        # Verificar estoque suficiente
        if produto.quantidade < quantidade:
            messages.error(request, f'Estoque insuficiente. Disponível: {produto.quantidade}, Solicitado: {quantidade}')
            return redirect('dashboard')
        
        with transaction.atomic():
            # Atualizar estoque
            produto.quantidade -= quantidade
            produto.save()
            
            # Criar registro de saída
            Saidas.objects.create(
                produto=produto,
                quantidade=quantidade,
                destino=destino,
                usuario=request.user
            )
            
            # Registrar movimentação
            Movimentacao.objects.create(
                tipo='RETIRADA',
                produto=produto,
                quantidade=quantidade,
                usuario=request.user,
                observacao=f'Retirada direta de {quantidade} unidades - Destino: {destino}'
            )
        
        messages.success(request, f'Retirada de {quantidade} unidades de {produto.nome} realizada com sucesso!')
        return redirect('dashboard')
    
    return redirect('dashboard')