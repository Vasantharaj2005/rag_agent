
# chains/qa_chain.py
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict, Any
from langchain.schema import Document
from loguru import logger
from core.config import settings

class QAChain:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            convert_system_message_to_human=True
        )
        self.qa_prompt = self._create_qa_prompt()
        self.chain = LLMChain(llm=self.llm, prompt=self.qa_prompt)
    
    def _create_qa_prompt(self) -> PromptTemplate:
        """Create the QA prompt template"""
        template = """You are an expert insurance policy analyst. Based on the provided context from a policy document, answer the question accurately and comprehensively.

Context Information:
{context}

Question: {question}

Instructions:
1. Provide a direct, factual answer based only on the information in the context
2. Include specific details like numbers, percentages, timeframes, waiting periods, and conditions
3. If the question asks about coverage, mention any limitations, exclusions, or special conditions
4. If the information is not clearly stated in the context, explicitly say "The document does not provide clear information about this"
5. Use the exact terminology from the policy document
6. Be concise but complete

Answer:"""
        
        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )
    
    async def answer_question(self, question: str, context_docs: List[Document]) -> str:
        """Answer a question based on context documents"""
        try:
            # Prepare context from documents
            context = self._prepare_context(context_docs)
            
            # Run the chain
            response = await self.chain.arun(
                context=context,
                question=question
            )
            
            logger.info(f"Generated answer for: {question[:50]}...")
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error in QA chain: {str(e)}")
            return f"Error generating answer: {str(e)}"
    
    def _prepare_context(self, documents: List[Document]) -> str:
        """Prepare context string from documents"""
        if not documents:
            return "No relevant context found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            # Include source information if available
            source_info = ""
            if "source" in doc.metadata:
                source_info = f" (Source: {doc.metadata['source']})"
            
            context_parts.append(f"Context {i}{source_info}:\n{doc.page_content}")
        
        return "\n\n".join(context_parts)




