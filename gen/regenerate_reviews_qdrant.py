"""Regenerate Qdrant reviews with dates matching orders (Jan 2025 - Jul 2026)."""

import json
import os
import random
import uuid
from pathlib import Path

import psycopg2
import qdrant_client
from dotenv import load_dotenv
from fastembed import TextEmbedding
from qdrant_client.models import Distance, PointStruct, VectorParams

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

random.seed(42)

COMMENTS = [
    "Produto chegou antes do prazo, estou muito satisfeito com a compra.",
    "Entrega atrasou mais de 10 dias, nao recebi nenhuma notificacao.",
    "O produto e exatamente como descrito na foto, otima qualidade.",
    "Frete absurdamente caro, quase o dobro do valor do produto.",
    "Ate hoje nao recebi meu pedido, faz 20 dias que comprei.",
    "Superou todas as minhas expectativas, recomendo muito.",
    "Produto chegou danificado, a embalagem estava completamente amassada.",
    "Atendimento ao cliente pessimo, ninguem resolve o problema.",
    "Entrega rapida e produto de otima qualidade, voltarei a comprar.",
    "O produto veio diferente da foto, cor totalmente errada.",
    "Demorou 15 dias para chegar, mas o produto e bom.",
    "Excelente custo-beneficio, produto de qualidade por um preco justo.",
    "Nao recebi o produto e o suporte nao responde meus chamados.",
    "Produto danificado na entrega, pedi reembolso mas nao obtive resposta.",
    "Chegou no prazo, embalagem bem protegida, produto perfeito.",
    "O frete demorou mais do que o esperado, porem o produto e bom.",
    "Comprei ha 3 semanas e ainda esta como pedido em processamento.",
    "Qualidade excelente, bem melhor do que esperava pelo preco.",
    "Produto veio com defeito de fabricacao, muito decepcionante.",
    "Entrega super rapida, recebi em 2 dias uteis. Recomendo o vendedor.",
    "O material e fraco, nao vale o preco que foi cobrado.",
    "Otimo produto, ja e minha segunda compra e continua me surpreendendo.",
    "A entrega estava prevista para sexta e chegou apenas na quarta da semana seguinte.",
    "Produto identico ao anunciado, funcionando perfeitamente.",
    "Tive que abrir disputa pois o produto nunca chegou no endereco.",
    "Muito bom, superou as expectativas em termos de qualidade e acabamento.",
    "Embalagem chegou aberta e produto com sinais de uso, inaceitavel.",
    "Rapido, seguro e produto de alta qualidade. Nota maxima.",
    "O vendedor nao fornece rastreamento atualizado, ficou dias sem movimentacao.",
    "Produto fantastico, vale cada centavo investido na compra.",
    "Pedido atrasou muito, o rastreamento nao atualizava e quase cancelei.",
    "Nao compro mais nessa loja, toda compra atrasa e o atendimento e pessimo.",
    "Moro no nordeste e a entrega demorou 25 dias, muito alem do prazo.",
    "Produto chegou depois do prazo estipulado, mas veio em perfeito estado.",
    "O frete para o nordeste e carissimo, quase desisti da compra.",
    "A entrega demorou porque a transportadora nao atende minha cidade no nordeste.",
    "Ja faz 30 dias que comprei e o pedido ainda nao chegou em Salvador.",
    "Moro em Recife e demorou 3 semanas para chegar, pessima experiencia.",
    "Pelo preco pago esperava mais, mas a demora na entrega foi o pior.",
    "O produto e bom mas a entrega para o nordeste e muito demorada.",
    "A transportadora perdeu meu pedido e tive que comprar outro.",
    "Excelente produto e entrega rapida ate em cidade pequena do nordeste.",
    "Chegou super rapido em Fortaleza, antes do prazo estipulado.",
    "Produto otimo e coube no orcamento, recomendo para quem mora no nordeste.",
    "Atrasou 2 dias mas valeu a pena, produto de otima qualidade.",
    "Nao recomendo, a entrega demorou muito e o produto veio errado.",
    "Produto maravilhoso, superou minhas expectativas, entrega otima.",
    "Pessimo atendimento, pedi cancelamento e nao foi resolvido.",
    "A embalagem veio violada, faltando pecas, muito descaso.",
    "O site e facil de usar, mas o frete e muito alto.",
    "Produto de baixa qualidade, quebrou em menos de uma semana.",
    "Nao recebi o codigo de rastreamento, precisei ligar no sac.",
    "O pedido chegou com 2 itens a menos, abri reclamacao.",
    "Muito satisfeito, entrega rapida e produto de primeira linha.",
    "Devolvi o produto e ate hoje nao recebi o reembolso.",
    "A loja trocou meu produto sem burocracia, otimo atendimento.",
    "O produto nao funcionou, acho que veio com defeito de fabrica.",
    "Chegou tudo certinho, bem embalado, dentro do prazo. Recomendo.",
    "O vendedor e muito atencioso, respondeu todas as duvidas.",
    "Produto excelente, mas a entrega poderia ser mais rapida.",
    "Paguei mais caro pelo frete express e chegou igual ao normal.",
    "Nao gostei, o produto parece de segunda linha, mal acabado.",
    "Atendimento rapido e eficiente, resolveram meu problema em minutos.",
    "O rastreamento parou de atualizar e fiquei dias sem noticias.",
    "Produto original e de qualidade, recomendo para todos.",
    "A garantia do produto e curta, deveria ser de no minimo 1 ano.",
    "Entregaram no vizinho, quase perdi o pedido, mas foi resolvido.",
    "Produto lindo, bem maior do que imaginei, amei a compra.",
    "A transportadora jogou a encomenda por cima do muro, absurdo.",
    "O sistema de pagamento falhou duas vezes, mas na terceira foi.",
    "Ja comprei varias vezes e nunca tive problemas, loja confiavel.",
    "O produto chegou amassado, parece que caiu durante o transporte.",
    "Otimo para presentear, veio bem embalado com papel de seda.",
    "Nao e exatamente como na foto, mas a qualidade e aceitavel.",
    "A descricao do produto nao condiz com a realidade, enganoso.",
    "Demorou mas chegou, e o produto realmente e bom como dizem.",
    "Fiquei muito feliz com a compra, chegou antes do natal.",
    "O produto nao encaixou direito, tive que adaptar em casa.",
    "Muito caro para a qualidade que entrega, nao vale o preco.",
    "A troca foi super facil, a loja enviou o novo antes de receber o antigo.",
    "O produto parece durar pouco, mas por enquanto esta funcionando.",
    "Atendimento pre-venda excelente, me ajudaram a escolher o tamanho certo.",
    "Chegou com cheiro de mofo, tive que deixar arejando por dias.",
    "Veio com manual so em ingles, dificil de configurar.",
    "A instalacao foi facil, veio com todos os parafusos e ferramentas.",
    "A politica de devolucao e complicada, nao recomendo para presentes.",
    "Produto de alto padrao, parece premium, valeu cada centavo.",
    "O site prometeu entrega em 2 dias, levou 10. Muito decepcionante.",
    "Produto resistente e bonito, uso diariamente e nao estragou.",
    "O vendedor demorou 5 dias para postar, mas depois chegou rapido.",
    "Amei a cor, veio exatamente como no site, tecido de qualidade.",
    "O suporte pos-venda e inexistente, precisei de ajuda e nao tive.",
    "Paguei o boleto e demorou 3 dias para confirmar o pagamento.",
    "A caixa chegou amassada mas o produto estava intacto, bem embalado.",
    "O desconto no pix valeu muito a pena, economia significativa.",
    "Prazo de entrega foi cumprido rigorosamente, parabens a loja.",
    "O produto tem um cheiro forte de plastico que nao sai.",
    "Muito bom pelo preco que paguei, nao esperava tanta qualidade.",
    "O produto veio com arranhao, parece que ja foi usado antes.",
    "Excelente atendimento pos-venda, resolveram tudo rapidamente.",
    "Comprei para meu filho e ele amou, brinquedo de qualidade.",
    "A entrega foi agendada e cumpriram o horario certinho.",
    "Produto muito pequeno, a foto engana, parecia maior no anuncio.",
    "O acabamento e impecavel, parece feito artesanalmente.",
    "Nao veio com nota fiscal, tive que solicitar depois da entrega.",
    "Sistema de pontos e recompensas e muito bom, vale a pena comprar.",
    "O produto e bonito mas e muito fragil, tem que manusear com cuidado.",
    "A qualidade do som e surpreendente para o tamanho do aparelho.",
    "Nao recomendo a transportadora, a entrega atrasou e veio violada.",
    "Otimo produto, mas o manual de instrucoes e muito confuso.",
    "A relacao qualidade preco e excelente, superou minhas expectativas.",
    "Mandei mensagem para o vendedor e ele respondeu em menos de 1 hora.",
    "Produto durou apenas 2 meses e comecou a apresentar defeitos.",
    "A compra foi facil e rapida, recomendo a loja para todos.",
    "O produto veio com a cor errada, mas a troca foi rapida.",
    "Produto de otimo acabamento, parece ser de alta durabilidade.",
    "Nao volto a comprar, experiencia pessima do inicio ao fim.",
    "A foto do produto nao mostra os detalhes reais, decepcionante.",
    "Chegou em perfeito estado, bem embalado e dentro do prazo.",
    "O produto e bonito mas o tamanho nao corresponde a tabela de medidas.",
    "A loja oferece garantia estendida por um precinho acessivel.",
    "O pagamento no cartao foi dividido sem juros, otima opcao.",
    "Produto muito versatil, uso em diversas ocasioes, vale a pena.",
    "A entrega demorou mas o produto e de qualidade, compensou.",
    "Nao gostei do tecido, parece que vai encolher na primeira lavagem.",
    "A experiencia de compra foi otima, site intuitivo e seguro.",
    "Produto veio com defeito oculto, so percebi depois de 1 semana.",
    "Comprei na promocao e chegou rapido, otima experiencia.",
    "Produto bem inferior ao anunciado, parece outra marca.",
    "Atendimento humanizado e atencioso, diferencial da loja.",
    "Produto original com lacre, veio tudo certinho, recomendo.",
    "A entrega foi rapida mas a embalagem veio aberta.",
    "Produto exatamente como esperado, compra segura e tranquila.",
    "O vendedor nao respeitou o prazo de entrega combinado.",
]

RATING_WEIGHTS = [0.05, 0.10, 0.20, 0.30, 0.35]


def main():
    conn = psycopg2.connect(
        host="localhost", dbname="shopagent", user="shopagent", password="shopagent",
    )

    # Fetch orders with dates and customer state
    cur = conn.cursor()
    cur.execute("""
        SELECT o.order_id, o.created_at, o.product_id, c.state
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        ORDER BY RANDOM()
    """)
    all_orders = [(row[0], row[1], row[2], row[3]) for row in cur.fetchall()]
    cur.close()
    conn.close()

    print(f"Total orders available: {len(all_orders)}")

    # Generate reviews for ~15% of orders (about 8000-9000 reviews)
    sample_size = int(len(all_orders) * 0.15)
    random.shuffle(all_orders)
    selected = all_orders[:sample_size]

    model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")

    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    client = qdrant_client.QdrantClient(url=qdrant_url, prefer_grpc=False)

    # Wipe and recreate collection
    collection = "shopagent_reviews"
    client.recreate_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )

    # Create payload indexes
    from qdrant_client.models import PayloadSchemaType
    client.create_payload_index(collection, "rating", PayloadSchemaType.INTEGER)
    client.create_payload_index(collection, "sentiment", PayloadSchemaType.KEYWORD)
    client.create_payload_index(collection, "created_at", PayloadSchemaType.KEYWORD)
    client.create_payload_index(collection, "product_id", PayloadSchemaType.KEYWORD)
    client.create_payload_index(collection, "customer_state", PayloadSchemaType.KEYWORD)

    BATCH_SIZE = 100
    points = []
    total = 0

    for order_id, created_at, product_id, customer_state in selected:
        rating = random.choices(range(1, 6), weights=RATING_WEIGHTS)[0]
        if rating >= 4:
            sentiment = "positive"
        elif rating == 3:
            sentiment = "neutral"
        else:
            sentiment = "negative"
        comment = random.choice(COMMENTS)

        review_text = json.dumps({
            "review_id": str(uuid.uuid4()),
            "order_id": str(order_id),
            "rating": rating,
            "comment": comment,
            "sentiment": sentiment,
            "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
            "product_id": str(product_id),
            "customer_state": customer_state,
        }, ensure_ascii=False)

        embedding = list(model.embed(comment))[0].tolist()

        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": review_text,
                "rating": rating,
                "sentiment": sentiment,
                "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
                "product_id": str(product_id),
                "customer_state": customer_state,
            },
        ))

        if len(points) >= BATCH_SIZE:
            client.upsert(collection_name=collection, points=points)
            total += len(points)
            print(f"  Upserted {total} reviews...")
            points = []

    if points:
        client.upsert(collection_name=collection, points=points)
        total += len(points)

    print(f"\nDone! {total} reviews upserted to Qdrant collection '{collection}'.")
    print(f"Date range: {selected[0][1]} to {selected[-1][1]}")


if __name__ == "__main__":
    main()
