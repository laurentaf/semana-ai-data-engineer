"""Generate full 2025-2026 order dataset (40k+ orders with historical dates)."""

import json
import random
import uuid
from datetime import datetime, timedelta

import psycopg2
import qdrant_client
from dotenv import load_dotenv
from fastembed import TextEmbedding
from qdrant_client.models import Distance, PointStruct, VectorParams, PayloadSchemaType

random.seed(42)

conn = psycopg2.connect(host="localhost", dbname="shopagent", user="shopagent", password="shopagent")
cur = conn.cursor()

# Fetch existing customers and products
cur.execute("SELECT customer_id FROM customers")
customer_ids = [row[0] for row in cur.fetchall()]
cur.execute("SELECT product_id, price FROM products")
products = [(row[0], float(row[1])) for row in cur.fetchall()]

print(f"Customers: {len(customer_ids)}, Products: {len(products)}")

# Generate orders with increasing monthly volume
def monthly_target(year, month):
    base = 200 + (year - 2025) * 3600 + month * 300
    return max(100, base + random.randint(-200, 300))

statuses = ["delivered", "shipped", "processing", "cancelled"]
status_w = [0.50, 0.20, 0.20, 0.10]
payments = ["credit_card", "pix", "boleto"]
payment_w = [0.40, 0.44, 0.16]

total_orders = 0
current = datetime(2025, 1, 1)
end = datetime(2026, 7, 13)

order_batch = []

while current <= end:
    y, m = current.year, current.month
    target = monthly_target(y, m)
    if m == 12:
        next_m = datetime(y + 1, 1, 1)
    else:
        next_m = datetime(y, m + 1, 1)
    days = (next_m - current).days

    for _ in range(target):
        day = random.randint(1, max(1, days))
        hour = random.randint(8, 22)
        minute = random.randint(0, 59)
        dt = datetime(y, m, day, hour, minute)
        if dt > end:
            continue

        cust_id = random.choice(customer_ids)
        prod_id, price = random.choice(products)
        qty = random.randint(1, 5)
        total = round(price * qty * random.uniform(0.85, 1.15), 2)
        status = random.choices(statuses, weights=status_w, k=1)[0]
        payment = random.choices(payments, weights=payment_w, k=1)[0]

        order_batch.append((
            str(uuid.uuid4()), str(cust_id), str(prod_id), qty, total, status, payment, dt,
        ))
        total_orders += 1

    current = next_m

print(f"Total to insert: {total_orders}")

# Insert in batches
BATCH_SIZE = 500
for i in range(0, len(order_batch), BATCH_SIZE):
    batch = order_batch[i:i + BATCH_SIZE]
    values = ",".join(
        cur.mogrify(
            "(%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s::timestamptz)",
            row,
        ).decode()
        for row in batch
    )
    cur.execute(f"INSERT INTO orders VALUES {values}")
    conn.commit()

print(f"Inserted {total_orders} orders with historical dates")

# Verify distribution
cur.execute("""
    SELECT TO_CHAR(created_at, 'YYYY-MM') AS mes, COUNT(*) AS pedidos,
    SUM(total)::numeric(12,2) AS faturamento
    FROM orders GROUP BY mes ORDER BY mes
""")
print("\nMonth       Orders  Revenue")
print("-" * 35)
for row in cur.fetchall():
    print(f"  {row[0]}  {str(row[1]):>6}  R$ {float(row[2]):>12,.2f}")

cur.close()
conn.close()

# ── Now ingest reviews into Qdrant ──────────────────────────────────────────
print("\nIngesting reviews into Qdrant...")

conn2 = psycopg2.connect(host="localhost", dbname="shopagent", user="shopagent", password="shopagent")
cur2 = conn2.cursor()
cur2.execute("""
    SELECT o.order_id, o.created_at, o.product_id, c.state
    FROM orders o JOIN customers c ON o.customer_id = c.customer_id
    ORDER BY RANDOM()
""")
all_orders = cur2.fetchall()
cur2.close()
conn2.close()

sample_size = min(int(len(all_orders) * 0.15), 12000)
random.shuffle(all_orders)
selected = all_orders[:sample_size]

model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")

client = qdrant_client.QdrantClient(url="http://localhost:6333", prefer_grpc=False)
collection = "shopagent_reviews"
client.recreate_collection(
    collection_name=collection,
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)
client.create_payload_index(collection, "rating", PayloadSchemaType.INTEGER)
client.create_payload_index(collection, "sentiment", PayloadSchemaType.KEYWORD)
client.create_payload_index(collection, "created_at", PayloadSchemaType.KEYWORD)
client.create_payload_index(collection, "product_id", PayloadSchemaType.KEYWORD)
client.create_payload_index(collection, "customer_state", PayloadSchemaType.KEYWORD)

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
    "Atendimento rapido e eficiente, resolveram meu problema em minutos.",
    "O rastreamento parou de atualizar e fiquei dias sem noticias.",
    "Produto original e de qualidade, recomendo para todos.",
    "A garantia do produto e curta, deveria ser de no minimo 1 ano.",
    "Produto lindo, bem maior do que imaginei, amei a compra.",
    "A transportadora jogou a encomenda por cima do muro, absurdo.",
    "Ja comprei varias vezes e nunca tive problemas, loja confiavel.",
    "O produto chegou amassado, parece que caiu durante o transporte.",
    "Otimo para presentear, veio bem embalado com papel de seda.",
    "A descricao do produto nao condiz com a realidade, enganoso.",
    "Demorou mas chegou, e o produto realmente e bom como dizem.",
    "Fiquei muito feliz com a compra, chegou antes do natal.",
    "A troca foi super facil, a loja enviou o novo antes de receber o antigo.",
    "Atendimento pre-venda excelente, me ajudaram a escolher o tamanho certo.",
    "Chegou com cheiro de mofo, tive que deixar arejando por dias.",
    "Veio com manual so em ingles, dificil de configurar.",
    "Produto de alto padrao, parece premium, valeu cada centavo.",
    "O site prometeu entrega em 2 dias, levou 10. Muito decepcionante.",
    "Produto resistente e bonito, uso diariamente e nao estragou.",
    "Paguei o boleto e demorou 3 dias para confirmar o pagamento.",
    "A compra foi facil e rapida, recomendo a loja para todos.",
    "O vendedor nao respeitou o prazo de entrega combinado.",
]

RATING_WEIGHTS = [0.05, 0.10, 0.20, 0.30, 0.35]

points = []
total_up = 0
BATCH = 100

for order_id, created_at, product_id, customer_state in selected:
    rating = random.choices(range(1, 6), weights=RATING_WEIGHTS)[0]
    sentiment = "positive" if rating >= 4 else ("neutral" if rating == 3 else "negative")
    comment = random.choice(COMMENTS)
    dt_str = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)

    review_text = json.dumps({
        "review_id": str(uuid.uuid4()),
        "order_id": str(order_id),
        "rating": rating,
        "comment": comment,
        "sentiment": sentiment,
        "created_at": dt_str,
        "product_id": str(product_id),
        "customer_state": customer_state,
    }, ensure_ascii=False)

    embedding = list(model.embed(comment))[0].tolist()
    points.append(PointStruct(
        id=str(uuid.uuid4()), vector=embedding,
        payload={"text": review_text, "rating": rating, "sentiment": sentiment,
                 "created_at": dt_str, "product_id": str(product_id), "customer_state": customer_state},
    ))
    if len(points) >= BATCH:
        client.upsert(collection_name=collection, points=points)
        total_up += len(points)
        points = []

if points:
    client.upsert(collection_name=collection, points=points)
    total_up += len(points)

print(f"\nDone! {total_up} reviews in Qdrant, {total_orders} orders in Postgres (2025-2026)")
