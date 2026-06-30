import hashlib
import re
import time
from functools import lru_cache
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from app.config import get_settings
from app.services.embeddings import embed_query, embed_texts


def log_timing(label: str, seconds: float) -> None:
    if get_settings().debug_timing:
        print(f"[timing] {label}: {seconds:.3f}s")


def normalize_collection_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_-]+", "-", name)
    name = name.strip("-_")

    if len(name) < 3:
        name = f"kb-{name or 'default'}"

    return name[:63]


def vector_to_pg(values: list[float]) -> str:
    return "[" + ",".join(str(float(v)) for v in values) + "]"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()

        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is missing.")

        self.pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            kwargs={
                "row_factory": dict_row,
                "prepare_threshold": None,
            },
            open=True,
        )

    def heartbeat(self) -> bool:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select 1 as ok")
                return cur.fetchone()["ok"] == 1

    def add_chunks(self, collection_name: str, chunks: list[str], metadatas: list[dict[str, Any]]) -> int:
        if not chunks:
            return 0

        collection = normalize_collection_name(collection_name)
        first_meta = metadatas[0] if metadatas else {}

        source_type = str(first_meta.get("source_type", "unknown"))
        source_name = str(first_meta.get("source_name", "unknown"))
        source_url = first_meta.get("source_url")

        joined_text = "\n\n".join(chunks)
        content_hash = text_hash(joined_text)

        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into rag_documents
                      (collection_name, source_type, source_name, source_url, content_hash, metadata)
                    values
                      (%s, %s, %s, %s, %s, %s)
                    on conflict (collection_name, source_type, source_name, content_hash)
                    do nothing
                    returning id
                    """,
                    (
                        collection,
                        source_type,
                        source_name,
                        source_url,
                        content_hash,
                        Jsonb({"chunks": len(chunks), "characters": len(joined_text)}),
                    ),
                )

                inserted_doc = cur.fetchone()

                if not inserted_doc:
                    return 0

                document_id = inserted_doc["id"]

                t0 = time.perf_counter()
                vectors = embed_texts(chunks)
                log_timing(f"embed {len(chunks)} chunks", time.perf_counter() - t0)

                rows = []

                for i, (chunk, vector, meta) in enumerate(zip(chunks, vectors, metadatas)):
                    chunk_index = int(meta.get("chunk_index", i))
                    chunk_metadata = dict(meta)
                    chunk_metadata["collection_name"] = collection

                    rows.append(
                        (
                            document_id,
                            collection,
                            str(meta.get("source_type", source_type)),
                            str(meta.get("source_name", source_name)),
                            chunk_index,
                            chunk,
                            len(chunk),
                            Jsonb(chunk_metadata),
                            vector_to_pg(vector),
                        )
                    )

                t1 = time.perf_counter()

                cur.executemany(
                    """
                    insert into rag_chunks
                      (document_id, collection_name, source_type, source_name, chunk_index, content, char_count, metadata, embedding)
                    values
                      (%s, %s, %s, %s, %s, %s, %s, %s, %s::extensions.vector)
                    """,
                    rows,
                )

                log_timing("postgres insert", time.perf_counter() - t1)

        return len(chunks)

    def query(self, collection_name: str, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        collection = normalize_collection_name(collection_name)

        t0 = time.perf_counter()
        q_vector = embed_query(question)
        log_timing("query embedding", time.perf_counter() - t0)

        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                t1 = time.perf_counter()

                cur.execute(
                    """
                    select
                      id,
                      document_id,
                      collection_name,
                      source_type,
                      source_name,
                      chunk_index,
                      content,
                      metadata,
                      similarity
                    from match_rag_chunks(%s::extensions.vector, %s, %s)
                    """,
                    (vector_to_pg(q_vector), top_k, collection),
                )

                rows = cur.fetchall()
                log_timing("postgres vector search", time.perf_counter() - t1)

        items: list[dict[str, Any]] = []

        for row in rows:
            metadata = dict(row.get("metadata") or {})
            metadata.setdefault("source_type", row["source_type"])
            metadata.setdefault("source_name", row["source_name"])
            metadata.setdefault("chunk_index", row["chunk_index"])
            metadata.setdefault("collection_name", row["collection_name"])
            metadata.setdefault("document_id", str(row["document_id"]))
            metadata.setdefault("chunk_id", str(row["id"]))

            items.append(
                {
                    "text": row["content"],
                    "metadata": metadata,
                    "score": None if row["similarity"] is None else round(float(row["similarity"]), 4),
                }
            )

        return items

    def list_collections(self) -> list[str]:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select distinct collection_name from rag_documents order by collection_name")
                return [row["collection_name"] for row in cur.fetchall()]

    def delete_collection(self, name: str) -> None:
        collection = normalize_collection_name(name)

        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from rag_documents where collection_name = %s", (collection,))

    def collection_stats(self, name: str) -> dict[str, Any]:
        collection = normalize_collection_name(name)

        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                      count(distinct d.id) as documents,
                      count(c.id) as chunks,
                      coalesce(sum(c.char_count), 0) as characters
                    from rag_documents d
                    left join rag_chunks c on c.document_id = d.id
                    where d.collection_name = %s
                    """,
                    (collection,),
                )

                row = cur.fetchone()

        return {
            "collection_name": collection,
            "documents": int(row["documents"] or 0),
            "chunks": int(row["chunks"] or 0),
            "characters": int(row["characters"] or 0),
        }


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    return VectorStore()