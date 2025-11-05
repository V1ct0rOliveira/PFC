from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth.decorators import login_required  
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decouple import config
from django.core.mail import send_mail
from .models import CustomUser, Product, Solicitacao, Movimentacao, Saidas, Entradas
from .views_log import registrar_log

# ============================================================================
# FUNÇÕES DE ESTOQUE - PRODUTOS
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
        
        produto = Product.objects.create(
            nome=nome,
            quantidade=quantidade,
            local=local,
            codigo=codigo,
            carencia=carencia
        )
        
        # Registrar log no banco
        registrar_log(
            acao="Produto cadastrado",
            usuario=request.user,
            detalhes=f"Cadastrou produto: {produto.nome} (Código: {produto.codigo})"
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
# FUNÇÕES DE ESTOQUE - MOVIMENTAÇÕES
# ============================================================================

@login_required
def listar_movimentacoes(request):
    """View para listar movimentações com filtros - BLOQUEADA para usuário comum"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    movimentacoes = Movimentacao.objects.select_related('produto').order_by('-data_hora')
    
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
        movimentacoes = movimentacoes.filter(usuario__icontains=usuario_id)
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
# FUNÇÕES DE ESTOQUE - SOLICITAÇÕES
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
            solicitante=request.user.username,
        )
        
        Movimentacao.objects.create(
            tipo='SOLICITACAO',
            produto=produto,
            quantidade=quantidade,
            usuario=request.user.username,
            referencia_id=solicitacao.id,
            observacao=f'Solicitação #{solicitacao.id} criada - Destino: {destino}'
        )
        
        # Registrar log no banco
        registrar_log(
            acao="Solicitação criada",
            usuario=request.user,
            detalhes=f"Solicitou {quantidade} unidades do produto: {produto.nome} - Destino: {destino}"
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
        solicitacao.aprovador = request.user.username
        solicitacao.data_aprovacao = timezone.now()
        solicitacao.save()
        
        produto.quantidade -= solicitacao.quantidade
        produto.save()
        
        Saidas.objects.create(
            produto=produto,
            quantidade=solicitacao.quantidade,
            destino=solicitacao.destino,
            usuario=request.user.username,
        )
        
        Movimentacao.objects.create(
            tipo='RETIRADA',
            produto=produto,
            quantidade=solicitacao.quantidade,
            usuario=request.user.username,
            referencia_id=solicitacao.id,
            observacao=f'Solicitação #{solicitacao.id} aprovada e retirada executada automaticamente - Destino: {solicitacao.destino}'
        )
        
        # Registrar log no banco
        registrar_log(
            acao="Solicitação aprovada",
            usuario=request.user.username,
            detalhes=f"Aprovou solicitação #{solicitacao.id} - {solicitacao.quantidade} unidades do produto: {produto.nome}"
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
    solicitacao.aprovador = request.user.username
    solicitacao.data_aprovacao = timezone.now()
    solicitacao.save()
    
    # Registrar log no banco
    registrar_log(
        acao="Solicitação reprovada",
        usuario=request.user.username,
        detalhes=f"Reprovou solicitação #{solicitacao.id} - {solicitacao.quantidade} unidades do produto: {solicitacao.produto.nome}"
    )
    
    messages.success(request, f'Solicitação #{solicitacao.id} reprovada!')
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

# ============================================================================
# FUNÇÕES DE ESTOQUE - ENTRADAS E SAÍDAS
# ============================================================================

@login_required
def entrada_produto(request):
    """View para entrada de produtos"""
    if request.method == 'POST':
        email = "beltramevictor13@gmail.com"
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
                usuario=request.user.username,
                observacao=f'Entrada de {quantidade} unidades'
            )

            Entradas.objects.create(
                produto=produto,
                quantidade=quantidade,
                usuario=request.user.username,
            )

            send_mail(
                'Entrada de Produto',
                f'O usuário {request.user.username} realizou a entrada de {quantidade} unidades do produto {produto.nome}.',
                'noreply@sistema.com',
                [email],
                fail_silently=True,
            )
            
            # Registrar log no banco
            registrar_log(
                acao="Entrada de produto",
                usuario=request.user.username,
                detalhes=f"Registrou entrada de {quantidade} unidades do produto: {produto.nome}"
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
        email = "beltramevictor13@gmail.com"
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
                usuario=request.user.username,
            )
            
            Movimentacao.objects.create(
                tipo='RETIRADA',
                produto=produto,
                quantidade=quantidade,
                usuario=request.user.username,
                observacao=f'Retirada direta de {quantidade} unidades - Destino: {destino}'
            )

            send_mail(
                'Retirada de Produto',
                f'O usuário {request.user.username} realizou a retirada de {quantidade} unidades do produto {produto.nome}.',
                'noreply@sistema.com',
                [email],
                fail_silently=True,
            )
            
            # Registrar log no banco
            registrar_log(
                acao="Retirada direta",
                usuario=request.user.username,
                detalhes=f"Retirou {quantidade} unidades do produto: {produto.nome} - Destino: {destino}"
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