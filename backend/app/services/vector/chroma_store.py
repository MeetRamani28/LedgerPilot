import anyio
from typing import Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.services.vector.base import IVectorStore
from app.core.config import settings


class ChromaVectorStore(IVectorStore):
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory if persist_directory is not None else settings.CHROMA_PERSIST_DIR
        self._client: Optional[chromadb.ClientAPI] = None

    def _get_client(self) -> chromadb.ClientAPI:
        if self._client is None:
            if not self.persist_directory or self.persist_directory == ":memory:":
                self._client = chromadb.EphemeralClient(
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
            else:
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
        return self._client

    def _get_or_create_collection(self, collection_name: str):
        client = self._get_client()
        return client.get_or_create_collection(name=collection_name)

    async def upsert(
        self,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        def _sync_upsert():
            collection = self._get_or_create_collection(collection_name)
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas if metadatas is not None else None,
            )

        await anyio.to_thread.run_sync(_sync_upsert)

    async def query_similar(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        def _sync_query() -> list[dict[str, Any]]:
            collection = self._get_or_create_collection(collection_name)
            kwargs: dict[str, Any] = {
                "query_texts": [query_text],
                "n_results": n_results,
            }
            if where:
                kwargs["where"] = where

            results = collection.query(**kwargs)
            matches: list[dict[str, Any]] = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0]
                docs = results["documents"][0] if results.get("documents") else []
                metas = results["metadatas"][0] if results.get("metadatas") else []
                dists = results["distances"][0] if results.get("distances") else []

                for i in range(len(ids)):
                    matches.append({
                        "id": ids[i],
                        "document": docs[i] if i < len(docs) else "",
                        "metadata": metas[i] if i < len(metas) else {},
                        "distance": dists[i] if i < len(dists) else 0.0,
                    })
            return matches

        return await anyio.to_thread.run_sync(_sync_query)

    async def delete(self, collection_name: str, ids: list[str]) -> None:
        def _sync_delete():
            collection = self._get_or_create_collection(collection_name)
            collection.delete(ids=ids)

        await anyio.to_thread.run_sync(_sync_delete)

    async def delete_collection(self, collection_name: str) -> None:
        def _sync_delete_col():
            client = self._get_client()
            try:
                client.delete_collection(name=collection_name)
            except Exception:
                pass

        await anyio.to_thread.run_sync(_sync_delete_col)
