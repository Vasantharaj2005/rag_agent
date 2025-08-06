
# utils/chunking.py
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.schema import Document
import tiktoken
from loguru import logger

class AdvancedChunker:
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 model_name: str = "gpt-3.5-turbo"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.encoding_for_model(model_name)
        
        # Different splitters for different content types
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        self.policy_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\nSection", "\n\nClause", "\n\n", "\n", ".", " ", ""]
        )
    
    def chunk_documents(self, documents: List[Document], content_type: str = "general") -> List[Document]:
        """Chunk documents based on content type"""
        try:
            if content_type == "policy":
                return self._chunk_policy_documents(documents)
            else:
                return self._chunk_general_documents(documents)
                
        except Exception as e:
            logger.error(f"Error chunking documents: {str(e)}")
            return documents
    
    def _chunk_general_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk general documents"""
        all_chunks = []
        
        for doc in documents:
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk.page_content),
                    "token_count": len(self.encoding.encode(chunk.page_content))
                })
            
            all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks
    
    def _chunk_policy_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk policy documents with special handling"""
        all_chunks = []
        
        for doc in documents:
            # Try to identify sections first
            sections = self._identify_policy_sections(doc.page_content)
            
            if sections:
                # Chunk by sections
                for section_name, section_content in sections.items():
                    section_doc = Document(
                        page_content=section_content,
                        metadata={**doc.metadata, "section": section_name}
                    )
                    
                    chunks = self.policy_splitter.split_documents([section_doc])
                    all_chunks.extend(chunks)
            else:
                # Regular chunking
                chunks = self.policy_splitter.split_documents([doc])
                all_chunks.extend(chunks)
        
        # Add token counts
        for chunk in all_chunks:
            chunk.metadata["token_count"] = len(self.encoding.encode(chunk.page_content))
        
        logger.info(f"Created {len(all_chunks)} policy chunks from {len(documents)} documents")
        return all_chunks
    
    def _identify_policy_sections(self, text: str) -> Dict[str, str]:
        """Identify common policy sections"""
        import re
        
        sections = {}
        current_section = None
        current_content = []
        
        # Common section headers
        section_headers = [
            r'^\s*(?:SECTION|Section)\s+\d+\s*[-:]?\s*(.+),
            r'^\s*(?:CLAUSE|Clause)\s+\d+\s*[-:]?\s*(.+),
            r'^\s*(\d+\.\s*.+),
            r'^\s*([A-Z][A-Z\s]+):\s*
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a section header
            is_header = False
            for pattern in section_headers:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous section
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = match.group(1).strip().lower()
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections if len(sections) > 1 else {}
    
    def optimize_chunks_for_retrieval(self, chunks: List[Document]) -> List[Document]:
        """Optimize chunks for better retrieval performance"""
        optimized_chunks = []
        
        for chunk in chunks:
            # Skip very short chunks
            if len(chunk.page_content.strip()) < 50:
                continue
            
            # Skip chunks that are mostly formatting
            if self._is_mostly_formatting(chunk.page_content):
                continue
            
            # Add context markers for better retrieval
            if "section" in chunk.metadata:
                chunk.page_content = f"Section: {chunk.metadata['section']}\n\n{chunk.page_content}"
            
            optimized_chunks.append(chunk)
        
        logger.info(f"Optimized {len(chunks)} chunks to {len(optimized_chunks)} chunks")
        return optimized_chunks
    
    def _is_mostly_formatting(self, text: str) -> bool:
        """Check if text is mostly formatting/whitespace"""
        text_chars = len(re.sub(r'\s', '', text))
        total_chars = len(text)
        
        return (text_chars / total_chars) < 0.3 if total_chars > 0 else True
