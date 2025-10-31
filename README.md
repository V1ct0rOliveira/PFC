# Sistema Web de Gerenciamento de Estoque

Sistema desenvolvido por **Victor Oliveira** e **Vinicius Nascimento**, com orientação de **Fabiano Bezerra**, como parte do bacharelado em Engenharia de Software na **Universidade de Mogi das Cruzes**.

## 🚀 Instalação e Configuração

### 1. Criar ambiente virtual
```bash
python -m venv venv
```

### 2. Ativar ambiente virtual
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Criar arquivo .env
Crie um arquivo `.env` na raiz do projeto com:
```bash
# Configurações do Supabase
DB_NAME=nome_do_database
DB_USER=nome_do_user
DB_PASSWORD=sua_senha
DB_HOST=host_do_banco
DB_PORT=porta_do_banco

# Configurações de Email
EMAIL_HOST_USER=email_do_site@gmail.com
EMAIL_HOST_PASSWORD=senha_app_do_email
EMAIL_PORT=porta_do_email
DEFAULT_FROM_EMAIL=email_do_site@gmail.com
```

### 5. Executar o sistema
```bash
# Comando único que inicia tudo
python manage.py runserver
```

**Acesse:**
- Interface Web: http://localhost:8000
- Admin Django: http://localhost:8000/admin

## 📊 Funcionalidades

### Níveis de Acesso
- **Usuário Comum**: Visualizar estoque e solicitar retiradas
- **Administrador**: Controle total do estoque e produtos
- **Superadministrador**: Todas as permissões + logs e gestão de usuários

### Recursos Principais
- 🟡 Gestão completa de produtos
- 🟡 Movimentações (entradas, saídas, ajustes)
- 🟡 Dashboard com estatísticas em tempo real
- 🟡 Notificações de estoque baixo
- 🟡 Relatórios em PDF, Excel e Word
- 🟡 Interface responsiva com Bootstrap 5
- 🟡 Logs de atividades detalhados

## 🔧 Tecnologias

- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: Bootstrap 5
- **Banco**: SQLite (desenvolvimento) / PostgreSQL supabase (produção)
- **Autenticação**: JWT e Authenticator
- **Relatórios**: python-docx, openpyxl, reportlab

## 📝 URLs Disponíveis

- **Interface Web**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin
