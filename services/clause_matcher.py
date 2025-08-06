
# services/clause_matcher.py
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from langchain.schema import Document
import re
from loguru import logger

class ClauseMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),
            max_features=1000
        )
    
    def find_relevant_clauses(
        self, 
        query: str, 
        documents: List[Document], 
        threshold: float = 0.3
    ) -> List[Tuple[Document, float]]:
        """Find clauses most relevant to the query using semantic similarity"""
        try:
            if not documents:
                return []
            
            # Extract text content
            texts = [doc.page_content for doc in documents]
            texts.append(query)  # Add query to the corpus
            
            # Compute TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Calculate similarity between query and documents
            query_vector = tfidf_matrix[-1]  # Last item is the query
            doc_vectors = tfidf_matrix[:-1]  # All except the query
            
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()
            
            # Create results with similarity scores
            results = []
            for i, similarity_score in enumerate(similarities):
                if similarity_score >= threshold:
                    results.append((documents[i], float(similarity_score)))
            
            # Sort by similarity score (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Found {len(results)} relevant clauses for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in clause matching: {str(e)}")
            return []
    
    def extract_specific_terms(self, text: str, term_patterns: Dict[str, str]) -> Dict[str, List[str]]:
        """Extract specific terms using regex patterns"""
        extracted_terms = {}
        
        for term_name, pattern in term_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            extracted_terms[term_name] = matches
        
        return extracted_terms
    
    def find_waiting_periods(self, text: str) -> List[str]:
        """Find waiting period mentions in text"""
        patterns = [
            r'waiting period of (\w+(?:\s+\w+)*)',
            r'(\d+)\s+(?:months?|years?|days?)\s+waiting period',
            r'wait(?:ing)?\s+(?:for\s+)?(\d+)\s+(?:months?|years?|days?)',
        ]
        
        waiting_periods = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            waiting_periods.extend(matches)
        
        return waiting_periods
    
    def find_coverage_limits(self, text: str) -> List[str]:
        """Find coverage limits and percentages"""
        patterns = [
            r'(?:limited to|capped at|maximum of|up to)\s+(\d+(?:\.\d+)?%?\s*(?:of\s+\w+(?:\s+\w+)*)?)',
            r'(\d+(?:\.\d+)?%)\s+(?:of|on)\s+\w+(?:\s+\w+)*',
            r'sum insured\s+(?:of\s+)?([^.]+)',
        ]
        
        limits = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            limits.extend(matches)
        
        return limits
