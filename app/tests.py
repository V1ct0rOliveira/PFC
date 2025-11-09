from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Solicitacao, Movimentacao, Entradas, Saidas, logs
from .views_log import registrar_log
from unittest.mock import patch
import json

User = get_user_model()

class ComprehensiveTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin', email='admin@test.com', password='test123', nivel_acesso='admin'
        )
        self.super_user = User.objects.create_user(
            username='super', email='super@test.com', password='test123', nivel_acesso='superadmin'
        )
        self.comum_user = User.objects.create_user(
            username='comum', email='comum@test.com', password='test123', nivel_acesso='comum'
        )
        self.produto = Product.objects.create(
            nome='Produto Teste', codigo='TEST001', quantidade=50, local='Estoque A', carencia=10
        )

    # Testes de Models
    def test_product_creation(self):
        self.assertEqual(str(self.produto), 'Produto Teste')
        self.assertEqual(self.produto.codigo, 'TEST001')

    def test_user_creation(self):
        self.assertEqual(self.admin_user.nivel_acesso, 'admin')
        self.assertTrue(self.admin_user.check_password('test123'))

    def test_solicitacao_creation(self):
        sol = Solicitacao.objects.create(
            produto=self.produto, quantidade=5, destino='TI', solicitante='admin'
        )
        self.assertEqual(sol.status, 'PENDENTE')

    def test_movimentacao_creation(self):
        mov = Movimentacao.objects.create(
            tipo='ENTRADA', produto=self.produto, quantidade=10, usuario='admin'
        )
        self.assertEqual(mov.tipo, 'ENTRADA')

    def test_entrada_creation(self):
        ent = Entradas.objects.create(produto=self.produto, quantidade=20, usuario='admin')
        self.assertEqual(ent.quantidade, 20)

    def test_saida_creation(self):
        sai = Saidas.objects.create(produto=self.produto, quantidade=5, destino='TI', usuario='admin')
        self.assertEqual(sai.destino, 'TI')

    def test_log_creation(self):
        log = logs.objects.create(acao='Teste', usuario='admin', detalhes='Teste log')
        self.assertEqual(log.acao, 'Teste')

    # Testes de Views Básicas
    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_login_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_post_valid(self):
        response = self.client.post(reverse('login'), {'username': 'admin', 'password': 'test123'})
        self.assertEqual(response.status_code, 302)

    def test_login_post_invalid(self):
        response = self.client.post(reverse('login'), {'username': 'wrong', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirect(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_admin(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('dashboard_admin'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_super(self):
        self.client.login(username='super', password='test123')
        response = self.client.get(reverse('dashboard_super'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_comum(self):
        self.client.login(username='comum', password='test123')
        response = self.client.get(reverse('dashboard_comum'))
        self.assertEqual(response.status_code, 200)

    # Testes de Produtos
    def test_estoque_geral(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('estoque_geral'))
        self.assertEqual(response.status_code, 200)

    def test_estoque_geral_filtros(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('estoque_geral'), {'codigo': 'TEST', 'nome': 'Produto'})
        self.assertEqual(response.status_code, 200)

    def test_cadastro_produto_get(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('cadastro_produto'))
        self.assertEqual(response.status_code, 200)

    def test_cadastro_produto_post(self):
        self.client.login(username='admin', password='test123')
        response = self.client.post(reverse('cadastro_produto'), {
            'nome': 'Novo', 'codigo': 'NEW001', 'quantidade': 100, 'local': 'Est B', 'carencia': 20
        })
        self.assertEqual(response.status_code, 302)

    def test_cadastro_produto_comum_denied(self):
        self.client.login(username='comum', password='test123')
        response = self.client.get(reverse('cadastro_produto'))
        self.assertEqual(response.status_code, 302)

    def test_deletar_produto(self):
        self.client.login(username='admin', password='test123')
        response = self.client.post(reverse('deletar_produto', args=[self.produto.id]))
        self.assertEqual(response.status_code, 302)

    def test_editar_produto(self):
        self.client.login(username='admin', password='test123')
        response = self.client.post(reverse('editar_produto', args=[self.produto.id]), {
            'nome': 'Editado', 'local': 'Novo Local', 'carencia': 15
        })
        self.assertEqual(response.status_code, 302)

    # Testes de Movimentações
    def test_listar_movimentacoes(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('listar_movimentacoes'))
        self.assertEqual(response.status_code, 200)

    def test_listar_movimentacoes_filtros(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('listar_movimentacoes'), {
            'codigo': 'TEST', 'usuario': 'admin', 'data_inicio': '2024-01-01'
        })
        self.assertEqual(response.status_code, 200)

    def test_listar_movimentacoes_comum_denied(self):
        self.client.login(username='comum', password='test123')
        response = self.client.get(reverse('listar_movimentacoes'))
        self.assertEqual(response.status_code, 302)

    # Testes de Solicitações
    @patch('app.views_product.EmailMultiAlternatives')
    def test_solicitar_produto(self, mock_email):
        mock_email.return_value.send.return_value = True
        self.client.login(username='admin', password='test123')
        response = self.client.post(reverse('solicitar_produto'), {
            'codigo': 'TEST001', 'quantidade': 5, 'destino': 'TI'
        })
        self.assertEqual(response.status_code, 302)

    def test_solicitar_produto_quantidade_zero(self):
        self.client.login(username='admin', password='test123')
        response = self.client.post(reverse('solicitar_produto'), {
            'codigo': 'TEST001', 'quantidade': 0, 'destino': 'TI'
        })
        self.assertEqual(response.status_code, 302)

    @patch('app.views_product.EmailMultiAlternatives')
    def test_entrada_produto(self, mock_email):
        mock_email.return_value.send.return_value = True
        self.client.login(username='admin', password='test123')
        response = self.client.post(reverse('entrada_produto'), {
            'codigo': 'TEST001', 'quantidade': 20
        })
        self.assertEqual(response.status_code, 302)

    # Testes de Usuários
    def test_perfil_get(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 200)

    def test_perfil_post(self):
        self.client.login(username='admin', password='test123')
        response = self.client.post(reverse('perfil'), {
            'nome': 'Novo Nome', 'sobrenome': 'Sobrenome', 'email': 'novo@test.com'
        })
        self.assertEqual(response.status_code, 302)

    def test_cadastro_get_super(self):
        self.client.login(username='super', password='test123')
        response = self.client.get(reverse('cadastro'))
        self.assertEqual(response.status_code, 200)

    def test_cadastro_admin_denied(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('cadastro'))
        self.assertEqual(response.status_code, 302)

    def test_tabela_usuarios_super(self):
        self.client.login(username='super', password='test123')
        response = self.client.get(reverse('tabela_usuarios'))
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_esqueci_senha_get(self):
        response = self.client.get(reverse('esqueci_senha'))
        self.assertEqual(response.status_code, 200)

    # Testes de Logs
    def test_logs_super_access(self):
        self.client.login(username='super', password='test123')
        response = self.client.get(reverse('logs'))
        self.assertEqual(response.status_code, 200)

    def test_logs_admin_denied(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('logs'))
        self.assertEqual(response.status_code, 302)

    def test_logs_filtros(self):
        self.client.login(username='super', password='test123')
        response = self.client.get(reverse('logs'), {
            'usuario': 'admin', 'data_inicio': '2024-01-01'
        })
        self.assertEqual(response.status_code, 200)

    def test_registrar_log_function(self):
        registrar_log('Teste Log', self.admin_user, 'Detalhes')
        log = logs.objects.first()
        self.assertEqual(log.acao, 'Teste Log')
        self.assertEqual(log.usuario, 'admin')

    # Testes de API
    def test_listar_produtos_api(self):
        response = self.client.get(reverse('listar_produtos_api'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('produtos', data)

    def test_detalhes_produto_api(self):
        response = self.client.get(reverse('detalhes_produtos_api', args=[self.produto.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['nome'], 'Produto Teste')

    def test_detalhes_produto_api_404(self):
        response = self.client.get(reverse('detalhes_produtos_api', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_listar_movimentacoes_api(self):
        response = self.client.get(reverse('listar_movimentacoes_api'))
        self.assertEqual(response.status_code, 200)

    # Testes de Relatórios
    def test_relatorio_pdf(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('relatorio_pdf_geral'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_relatorio_excel(self):
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('relatorio_excel_geral'))
        self.assertEqual(response.status_code, 200)

    def test_relatorio_not_logged(self):
        response = self.client.get(reverse('relatorio_pdf_geral'))
        self.assertEqual(response.status_code, 302)