from abc import ABC, abstractmethod
from typing import Any, Optional


class IVectorStore(ABC):
    @abstractmethod
    async def upsert(
        self,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """Upsert documents with IDs and optional metadata."""
        pass

    @abstractmethod
    async def query_similar(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Query for nearest documents. Returns list of matches with id, document, metadata, distance."""
        pass

    @abstractmethod
    async def delete(self, collection_name: str, ids: list[str]) -> None:
        """Delete specific documents by ID."""
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """Delete entire collection."""
        pass
