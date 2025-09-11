# Importações necessárias do Django
from django.shortcuts import render, redirect  # Para renderizar templates e redirecionar
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout  # Sistema de autenticação
from django.contrib.auth.decorators import login_required  # Decorator para proteger views
from django.contrib import messages  # Sistema de mensagens para feedback ao usuário
from .models import CustomUser, Product  # Modelos personalizados da aplicação

def home(request):
    """View da página inicial do sistema"""
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
            # Login bem-sucedido, redireciona para dashboard
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
    return render(request, 'dashboard.html')

def logout(request):
    """View para logout do usuário"""
    auth_logout(request)  # Encerra a sessão do usuário
    return redirect('home')  # Redireciona para página inicial

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