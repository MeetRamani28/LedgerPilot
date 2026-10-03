import os
from typing import Optional
import uuid
from pathlib import Path
import anyio
from app.core.config import settings
from app.services.storage.base import IStorageService


class LocalStorageService(IStorageService):
    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/pdf",
    ) -> tuple[str, str]:
        # Generate safe unique key
        import re
        safe_stem = re.sub(r'[^\w\-_\.]', '_', Path(filename).stem)
        ext = Path(filename).suffix or ".pdf"
        unique_name = f"{uuid.uuid4().hex}_{safe_stem}{ext}"
        target_path = self.upload_dir / unique_name

        def _write():
            with open(target_path, "wb") as f:
                f.write(file_bytes)

        await anyio.to_thread.run_sync(_write)
        storage_key = unique_name
        file_url = f"/api/v1/invoices/file/{storage_key}"
        return file_url, storage_key

    async def download(self, storage_key: str) -> bytes:
        target_path = self.upload_dir / storage_key
        if not target_path.exists():
            raise FileNotFoundError(f"Storage file not found: {storage_key}")

        def _read():
            with open(target_path, "rb") as f:
                return f.read()

        return await anyio.to_thread.run_sync(_read)

    async def delete(self, storage_key: str) -> bool:
        target_path = self.upload_dir / storage_key
        if target_path.exists():
            def _remove():
                target_path.unlink(missing_ok=True)

            await anyio.to_thread.run_sync(_remove)
            return True
        return False
