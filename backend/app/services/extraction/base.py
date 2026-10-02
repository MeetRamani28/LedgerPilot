from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.invoice_extraction import ExtractedInvoice


class IExtractionService(ABC):
    @abstractmethod
    async def extract_invoice(
        self,
        pdf_bytes: bytes,
        filename: Optional[str] = None,
    ) -> ExtractedInvoice:
        """Extract structured invoice data from raw PDF bytes."""
        pass
