from typing import Optional
import json
import cohere
from tenacity import retry, stop_after_attempt, wait_random_exponential
from app.core.config import settings
from app.schemas.invoice_extraction import ExtractedInvoice
from app.services.extraction.base import IExtractionService
from app.services.extraction.pdf_utils import pdf_to_base64_images

EXTRACTION_PROMPT = """Extract the invoice information as JSON with keys:
invoice_number, vendor_name, vendor_tax_id, vendor_address, invoice_date, due_date, purchase_order_number, currency, line_items, subtotal, tax_amount, total_amount, payment_terms.
Line items must each have: line_number, description, quantity, unit_price, total_amount, po_line_reference.
Ensure exact arithmetic: quantity * unit_price = total_amount, sum of line totals = subtotal, subtotal + tax = total_amount.
Return JSON only.
"""


class CohereExtractor(IExtractionService):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.COHERE_API_KEY
        self.client = cohere.AsyncClientV2(api_key=self.api_key)

    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def extract_invoice(
        self,
        pdf_bytes: bytes,
        filename: Optional[str] = None,
    ) -> ExtractedInvoice:
        images = pdf_to_base64_images(pdf_bytes, max_pages=1)
        if not images:
            raise ValueError("No images extracted from PDF")

        response = await self.client.chat(
            model="command-r-plus-08-2024",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{images[0]}"},
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
        )

        content = response.message.content[0].text
        return ExtractedInvoice.model_validate_json(content)
