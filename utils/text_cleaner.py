
# utils/text_cleaner.py
import re
from typing import List, Dict
import unicodedata

class TextCleaner:
    def __init__(self):
        # Common patterns to clean
        self.patterns = {
            'extra_whitespace': re.compile(r'\s+'),
            'page_numbers': re.compile(r'Page\s+\d+\s*(?:of\s*\d+)?', re.IGNORECASE),
            'headers_footers': re.compile(r'^.*(?:header|footer|page|©|\(c\)).*$', re.IGNORECASE | re.MULTILINE),
            'bullet_points': re.compile(r'^\s*[•·▪▫‣⁃]\s*', re.MULTILINE),
            'numbered_lists': re.compile(r'^\s*\d+\.\s*', re.MULTILINE),
            'urls': re.compile(r'https?://[^\s]+'),
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        }
    
    def clean_text(self, text: str, aggressive: bool = False) -> str:
        """Clean text with various preprocessing steps"""
        if not text:
            return ""
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove page numbers
        text = self.patterns['page_numbers'].sub('', text)
        
        # Remove headers/footers (if aggressive)
        if aggressive:
            text = self.patterns['headers_footers'].sub('', text)
        
        # Clean bullet points and numbered lists
        text = self.patterns['bullet_points'].sub('• ', text)
        text = self.patterns['numbered_lists'].sub('', text)
        
        # Remove URLs (if aggressive)
        if aggressive:
            text = self.patterns['urls'].sub('[URL]', text)
            text = self.patterns['emails'].sub('[EMAIL]', text)
        
        # Clean extra whitespace
        text = self.patterns['extra_whitespace'].sub(' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_policy_sections(self, text: str) -> Dict[str, str]:
        """Extract common policy sections"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            'definitions': r'definitions?\s*:?\s*(.*?)(?=\n[A-Z\s]+:|\n\d+\.|\Z)',
            'coverage': r'coverage\s*:?\s*(.*?)(?=\n[A-Z\s]+:|\n\d+\.|\Z)',
            'exclusions': r'exclusions?\s*:?\s*(.*?)(?=\n[A-Z\s]+:|\n\d+\.|\Z)',
            'waiting_period': r'waiting\s+period\s*:?\s*(.*?)(?=\n[A-Z\s]+:|\n\d+\.|\Z)',
            'claims': r'claims?\s*:?\s*(.*?)(?=\n[A-Z\s]+:|\n\d+\.|\Z)',
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section_name] = self.clean_text(match.group(1))
        
        return sections
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter sentences
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Filter very short sentences
                clean_sentences.append(sentence)
        
        return clean_sentences
