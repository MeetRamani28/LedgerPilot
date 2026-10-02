import json
from typing import Optional
from groq import AsyncGroq, RateLimitError, APIError
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from app.core.config import settings
from app.schemas.invoice_extraction import ExtractedInvoice
from app.services.extraction.base import IExtractionService
from app.services.extraction.pdf_utils import pdf_to_base64_images

EXTRACTION_SYSTEM_PROMPT = """You are an expert accounts payable AI agent. Your job is to extract all structured data from the provided invoice document with 100% precision.
Return a valid JSON object matching this exact schema:
{
  "invoice_number": "string",
  "vendor_name": "string",
  "vendor_tax_id": "string or null",
  "vendor_address": "string or null",
  "invoice_date": "YYYY-MM-DD or string or null",
  "due_date": "YYYY-MM-DD or string or null",
  "purchase_order_number": "string or null",
  "currency": "USD or ISO currency code",
  "line_items": [
    {
      "line_number": 1,
      "description": "item description",
      "quantity": 1.0,
      "unit_price": 10.0,
      "total_amount": 10.0,
      "po_line_reference": "optional reference or null"
    }
  ],
  "subtotal": 100.0,
  "tax_amount": 10.0,
  "total_amount": 110.0,
  "payment_terms": "Net 30 or null"
}

Important Rules:
1. Ensure the arithmetic is exact: line item quantity * unit_price = total_amount.
2. Sum of line item totals must equal subtotal.
3. Subtotal + tax_amount must equal total_amount.
4. Output JSON only. Do not include markdown codeblocks or conversational text.
"""


class GroqVisionExtractor(IExtractionService):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_VISION_MODEL
        self.client = AsyncGroq(api_key=self.api_key)

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIError)),
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def _call_groq_vision(self, base64_image: str) -> str:
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all data from this invoice page into the required structured JSON format.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            },
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        return response.choices[0].message.content or "{}"

    async def extract_invoice(
        self,
        pdf_bytes: bytes,
        filename: Optional[str] = None,
    ) -> ExtractedInvoice:
        # Convert PDF page 1 to base64 image
        images = pdf_to_base64_images(pdf_bytes, max_pages=1)
        if not images:
            raise ValueError("Unable to rasterize PDF for vision extraction.")

        raw_json_str = await self._call_groq_vision(images[0])
        # Clean any accidental wrapping
        raw_json_str = raw_json_str.strip()
        if raw_json_str.startswith("```json"):
            raw_json_str = raw_json_str.removeprefix("```json").removesuffix("```").strip()
        elif raw_json_str.startswith("```"):
            raw_json_str = raw_json_str.removeprefix("```").removesuffix("```").strip()

        # Strict validation through Pydantic v2
        return ExtractedInvoice.model_validate_json(raw_json_str)
