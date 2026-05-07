"""ShopAgent Day 2 — Query The Memory (Qdrant) without re-indexing."""

import os
from pathlib import Path

import qdrant_client
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex, Response
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.vector_stores.qdrant import QdrantVectorStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

_settings_initialized = False


def _configure_settings() -> None:
    global _settings_initialized
    if _settings_initialized:
        return
    Settings.llm = Anthropic(model="claude-sonnet-4-20250514")
    Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")
    _settings_initialized = True


def query_reviews(
    question: str,
    qdrant_url: str | None = None,
    collection_name: str | None = None,
    top_k: int = 5,
) -> Response:
    _configure_settings()
    qdrant_url = qdrant_url or os.environ.get("QDRANT_URL", "http://localhost:6333")
    collection_name = collection_name or os.environ.get("QDRANT_COLLECTION", "shopagent_reviews")

    client = qdrant_client.QdrantClient(url=qdrant_url, check_compatibility=False)
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)

    index = VectorStoreIndex.from_vector_store(vector_store)
    engine = index.as_query_engine(similarity_top_k=top_k)
    return engine.query(question)


DEMO_QUERIES = [
    "Clientes reclamando de entrega atrasada",
    "Reviews positivos sobre qualidade do produto",
    "Problemas com pagamento ou frete",
]

if __name__ == "__main__":
    for q in DEMO_QUERIES:
        print(f"\n{'='*60}")
        print(f"  Q: {q}")
        print(f"{'='*60}")
        response = query_reviews(q)
        print(f"  A: {response.response}")
        print(f"\n  Sources ({len(response.source_nodes)} chunks):")
        for node in response.source_nodes:
            print(f"    [{node.score:.3f}] {node.text[:100]}...")
