# services/document_loader.py
import aiohttp
import tempfile
import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import UnstructuredEmailLoader
from langchain_community.embeddings import GooglePalmEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from loguru import logger
from core.config import settings
import mimetypes
from urllib.parse import urlparse

class DocumentLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    async def load_from_url(self, url: str) -> List[Document]:
        """Download document from URL and process it"""
        try:
            logger.info(f"Downloading document from: {url}")
            
            # Download file
            temp_file_path = await self._download_file(url)
            
            # Determine file type and load appropriately
            documents = await self._load_document(temp_file_path, url)
            
            # Split documents into chunks
            split_docs = self.text_splitter.split_documents(documents)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            logger.info(f"Loaded and split document into {len(split_docs)} chunks")
            return split_docs
            
        except Exception as e:
            logger.error(f"Error loading document from URL: {str(e)}")
            raise
    
    async def _download_file(self, url: str) -> str:
        """Download file from URL to temporary location"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download file: HTTP {response.status}")
                
                # Get file extension from URL or content type
                parsed_url = urlparse(url)
                file_extension = os.path.splitext(parsed_url.path)[1]
                
                if not file_extension:
                    content_type = response.headers.get('Content-Type', '')
                    file_extension = mimetypes.guess_extension(content_type.split(';')[0]) or ''
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=file_extension
                ) as temp_file:
                    async for chunk in response.content.iter_chunked(8192):
                        temp_file.write(chunk)
                    return temp_file.name
    
    async def _load_document(self, file_path: str, original_url: str) -> List[Document]:
        """Load document based on file type"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension in ['.docx', '.doc']:
                loader = Docx2txtLoader(file_path)
            elif file_extension in ['.eml', '.msg']:
                loader = UnstructuredEmailLoader(file_path)
            else:
                # Try to load as plain text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return [Document(
                    page_content=content,
                    metadata={"source": original_url, "file_type": file_extension}
                )]
            
            documents = loader.load()
            
            # Add metadata
            for doc in documents:
                doc.metadata.update({
                    "source": original_url,
                    "file_type": file_extension
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document with extension {file_extension}: {str(e)}")
            raise
