# services/vector_store.py
from pinecone import Pinecone  # MODIFIED: Import the Pinecone class
import uuid
from typing import List, Optional
from langchain.schema import Document
from langchain_community.vectorstores import Pinecone as LangchainPinecone # RENAMED: To avoid confusion
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from loguru import logger
from core.config import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pinecone import ServerlessSpec

class VectorStoreManager:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY) # NEW: Initialize client here
        self.index = None
        self.vector_store = None
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def initialize(self):
        """Initialize Pinecone connection"""
        try:
            # MODIFIED: The client is now initialized in __init__.
            # We now use the self.pc instance for all operations.
            index_name = settings.PINECONE_INDEX_NAME
            
            # Check if index exists, create if not
            if index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating new Pinecone index: {index_name}")
                self.pc.create_index(
                    name=index_name,
                    dimension=settings.VECTOR_DIMENSION,
                    metric="cosine",    
                    spec=ServerlessSpec(
                        cloud=settings.PINECONE_CLOUD,         # or "gcp"
                        region=settings.PINECONE_ENVIRONMENT   # or your Pinecone region
                    )
                )
            
            self.index = self.pc.Index(index_name)
            
            # Initialize LangChain's Pinecone vector store
            # Using the renamed import to avoid ambiguity
            self.vector_store = LangchainPinecone(
                index=self.index,
                embedding=self.embeddings, # MODIFIED: Pass the full embedding object
                text_key="text"
            )
            
            logger.info("Pinecone vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to vector store"""
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            doc_ids = [str(uuid.uuid4()) for _ in documents]
            
            batch_size = 10
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_ids = doc_ids[i:i+batch_size]
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.executor,
                    # MODIFIED: Use the 'from_documents' class method for clarity and correctness
                    lambda: self.vector_store.add_documents(
                        documents=batch_docs, 
                        ids=batch_ids
                    )
                )
                
                logger.info(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            logger.info(f"Successfully added {len(documents)} documents with IDs: {doc_ids[:5]}...")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    # ... The rest of your methods (similarity_search, etc.) are correct and do not need changes ...
    async def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """Perform similarity search"""
        try:
            if not self.vector_store:
                raise Exception("Vector store not initialized")
            
            k = k or settings.TOP_K_RESULTS
            
            # Run search in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                lambda: self.vector_store.similarity_search(
                    query, 
                    k=k
                )
            )
            
            logger.info(f"Found {len(results)} similar documents for query: {query[:100]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            raise
    
    async def similarity_search_with_score(self, query: str, k: int = None) -> List[tuple]:
        """Perform similarity search with relevance scores"""
        try:
            if not self.vector_store:
                raise Exception("Vector store not initialized")
            
            k = k or settings.TOP_K_RESULTS
            
            # Run search in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                lambda: self.vector_store.similarity_search_with_score(
                    query, 
                    k=k
                )
            )
            
            # Filter by similarity threshold
            filtered_results = [
                (doc, score) for doc, score in results 
                if score >= settings.SIMILARITY_THRESHOLD
            ]
            
            logger.info(f"Found {len(filtered_results)} relevant documents (threshold: {settings.SIMILARITY_THRESHOLD})")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error performing similarity search with score: {str(e)}")
            raise
    
    async def cleanup(self, doc_ids: List[str]):
        """Clean up documents from vector store"""
        try:
            if doc_ids and self.index:
                logger.info(f"Cleaning up {len(doc_ids)} documents from vector store")
                
                # Run cleanup in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.executor,
                    lambda: self.index.delete(ids=doc_ids)
                )
                
                logger.info("Cleanup completed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            # Don't raise exception for cleanup errors