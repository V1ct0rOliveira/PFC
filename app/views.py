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