from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class CustomUser(AbstractUser):
    # Modelo da tabela de usuário que estende o AbstractUser do Django
    # Adiciona campos específicos para o sistema de estoque
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    nivel_acesso = models.CharField(max_length=50)
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    totp_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    
class Product(models.Model):
    # Modelo da tabela produtos
    # Contém todas as informações necessárias para gerenciar produtos
    nome = models.CharField(max_length=100)
    quantidade = models.IntegerField(default=0)
    local = models.CharField(max_length=100)
    codigo = models.CharField(max_length=100, unique=True)
    carencia = models.IntegerField(default=0)

    def __str__(self):
        return self.nome
    
class Entradas(models.Model):
    # Model da tabela de entradas de produtos
    # Contém informações sobre as entradas de produtos
    produto = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    data_entrada = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150)

    def __str__(self):
        return f"Entrada de {self.quantidade} de {self.produto.nome} por {self.usuario} em {self.data_entrada}"
    
class Saidas(models.Model):
    # Model da tabela de saídas de produtos
    # Contém informações sobre as saídas de produtos
    produto = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    destino = models.CharField(max_length=200, help_text="Para onde o produto será destinado", default="Não especificado")
    data_saida = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150)

    def __str__(self):
        return f"Saída de {self.quantidade} de {self.produto.nome} por {self.usuario} em {self.data_saida}"

class Solicitacao(models.Model):
    # Model da tabela de solicitações de produtos
    # Contém informações sobre as solicitações feitas pelos usuários
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('REPROVADA', 'Reprovada'),
        ('ATENDIDA', 'Atendida'),
    ]
    
    produto = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    destino = models.CharField(max_length=200, help_text="Para onde o produto será destinado", default="Não especificado")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    solicitante = models.CharField(max_length=150)
    aprovador = models.CharField(max_length=150, blank=True, null=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Solicitação {self.id} - {self.produto.nome} - {self.status}"

class Movimentacao(models.Model):
    # Model da tabela de movimentações de produtos
    # Contém um histórico detalhado de todas as movimentações de produtos
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SOLICITACAO', 'Solicitação'),
        ('APROVACAO', 'Aprovação'),
        ('RETIRADA', 'Retirada'),
    ]
    
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    produto = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantidade = models.IntegerField(null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150)
    referencia_id = models.IntegerField(null=True, blank=True) 
    observacao = models.TextField(blank=True)

    def __str__(self):
        return f"{self.tipo} - {self.produto.nome} - {self.data_hora}"   

class logs (models.Model):
    # Model da tabela de logs de ações do sistema
    # Contém informações sobre ações realizadas pelos usuários no sistema
    acao = models.CharField(max_length=200)
    usuario = models.CharField(max_length=150)
    data_hora = models.DateTimeField(auto_now_add=True)
    detalhes = models.TextField(blank=True)

    def __str__(self):
        return f"Log {self.id} - {self.acao} por {self.usuario} em {self.data_hora}"