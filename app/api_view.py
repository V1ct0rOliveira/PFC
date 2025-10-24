from django.http import JsonResponse
from .models import Product, Movimentacao

def listar_produtos_api(request):
    produtos = Product.objects.all()
    data = [{"id": produto.id, "nome": produto.nome, "quantidade": produto.quantidade, "codigo": produto.codigo} for produto in produtos]
    return JsonResponse(data, safe=False)

def detalhes_produtos_api(request, product_id):
    try:
        produto = Product.objects.get(id=product_id)
        data = {"id": produto.id, "nome": produto.nome, "quantidade": produto.quantidade, "local": produto.local, "codigo": produto.codigo, "carencia": produto.carencia}
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Produto não encontrado"}, status=404)

def listar_movimentacoes_api(request):
    movimentacoes = Movimentacao.objects.all()
    data = [{
        "id": mov.id,
        "produto": mov.produto.nome,
        "tipo": mov.tipo,
        "quantidade": mov.quantidade,
        "data_hora": mov.data_hora.isoformat(), 
        "observacao": mov.observacao,
    } for mov in movimentacoes]
    return JsonResponse(data, safe=False)

def detalhes_movimentacoes_api(request, movimentacao_id):
    try:
        mov = Movimentacao.objects.get(id=movimentacao_id)
        data = {
            "id": mov.id,
            "produto": mov.produto.nome,
            "tipo": mov.tipo,
            "quantidade": mov.quantidade,
            "data_hora": mov.data_hora.isoformat(), 
            "observacao": mov.observacao,
        }
        return JsonResponse(data)
    except Movimentacao.DoesNotExist:
        return JsonResponse({"error": "Movimentação não encontrada"}, status=404)