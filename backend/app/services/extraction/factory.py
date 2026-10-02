from typing import Optional
from app.core.config import settings
from app.services.extraction.base import IExtractionService
from app.services.extraction.mock_extractor import MockExtractor
from app.services.extraction.groq_extractor import GroqVisionExtractor
from app.services.extraction.cohere_extractor import CohereExtractor


def get_extraction_service(provider: Optional[str] = None) -> IExtractionService:
    provider = provider or settings.EXTRACTION_PROVIDER.lower()

    if provider == "groq":
        return GroqVisionExtractor()
    elif provider == "cohere":
        return CohereExtractor()
    elif provider == "mock":
        return MockExtractor()
    else:
        # Default fallback to mock for safety
        return MockExtractor()
