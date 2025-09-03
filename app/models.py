from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15)
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    nivel_acesso = models.CharField(max_length=50)

    def __str__(self):
        return self.username