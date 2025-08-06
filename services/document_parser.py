# services/document_parser.py
from loguru import logger
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from google.cloud import documentai

from core.config import settings

class AdvancedDocumentParser:
    """
    A service dedicated to parsing complex documents into clean, structured text
    using the Google Document AI service.
    """
    def __init__(self):
        # The Google client library uses the environment variable for auth.
        # It's synchronous, so we'll use an executor to run it in our async app.
        self.client = documentai.DocumentProcessorServiceClient()
        self.processor_name = settings.DOCUMENTAI_PROCESSOR_NAME
        self.executor = ThreadPoolExecutor(max_workers=2)
        logger.info("AdvancedDocumentParser initialized with Google Document AI client.")

    def _process_with_doc_ai(self, content: bytes) -> str:
        """Synchronous helper function that calls the Document AI API."""
        raw_document = documentai.RawDocument(content=content, mime_type="application/pdf")
        request = documentai.ProcessRequest(name=self.processor_name, raw_document=raw_document)
        
        result = self.client.process_document(request=request)
        
        return result.document.text

    async def parse(self, document_url: str) -> str:
        """
        Downloads a document and parses it into clean text using Google Document AI.
        """
        logger.info(f"Starting advanced parsing for document: {document_url}")
        
        # 1. Download the document content asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.get(document_url) as response:
                response.raise_for_status()
                content = await response.read()

        # 2. Process the document with Document AI in a thread pool to avoid blocking
        logger.info("Parsing document with Google Document AI...")
        try:
            loop = asyncio.get_event_loop()
            clean_text = await loop.run_in_executor(
                self.executor, self._process_with_doc_ai, content
            )
            
            logger.info(f"Document AI successfully extracted {len(clean_text)} characters.")
            return clean_text
            
        except Exception as e:
            logger.error(f"Google Document AI parsing failed: {e}")
            raise ValueError("Failed to parse document with Document AI.")