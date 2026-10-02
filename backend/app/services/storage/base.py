from abc import ABC, abstractmethod


class IStorageService(ABC):
    @abstractmethod
    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/pdf",
    ) -> tuple[str, str]:
        """Upload file bytes. Returns tuple: (public_or_stream_url, storage_key)."""
        pass

    @abstractmethod
    async def download(self, storage_key: str) -> bytes:
        """Download raw bytes by storage key."""
        pass

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Delete file by storage key."""
        pass
