# Importações necessárias do Django
from django.db import models  # Para criar modelos de banco de dados
from django.contrib.auth.models import AbstractUser  # Modelo base para usuários personalizados

class CustomUser(AbstractUser):
    # Modelo da tabela de usuário que estende o AbstractUser do Django
    # Adiciona campos específicos para o sistema de estoque
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15)
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    nivel_acesso = models.CharField(max_length=50)

    def __str__(self):
        # Retorna o username como representação string do objeto
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
        # Retorna o nome do produto como representação string do objeto
        return self.nome
    
class Entradas(models.Model):
    # Model da tabela de entradas de produtos
    # Contém informações sobre as entradas de produtos
    produto = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    data_entrada = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        # Retorna uma string representando a entrada
        return f"Entrada de {self.quantidade} de {self.produto.nome} por {self.usuario.username} em {self.data_entrada}"
    
class Saidas(models.Model):
    # Model da tabela de saídas de produtos
    # Contém informações sobre as saídas de produtos
    produto = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    data_saida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        # Retorna uma string representando a saída
        return f"Saída de {self.quantidade} de {self.produto.nome} por {self.usuario.username} em {self.data_saida}"