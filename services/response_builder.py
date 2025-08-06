
# services/response_builder.py
from typing import List, Dict, Any
from models.request_response import RAGResponse
from loguru import logger
import json

class ResponseBuilder:
    def __init__(self):
        pass
    
    def build_response(self, answers: List[str]) -> RAGResponse:
        """Build structured response from answers"""
        try:
            # Clean and format answers
            formatted_answers = []
            
            for answer in answers:
                # Clean up the answer
                cleaned_answer = self._clean_answer(answer)
                formatted_answers.append(cleaned_answer)
            
            response = RAGResponse(answers=formatted_answers)
            
            logger.info(f"Built response with {len(formatted_answers)} answers")
            return response
            
        except Exception as e:
            logger.error(f"Error building response: {str(e)}")
            # Return error response
            return RAGResponse(answers=[f"Error processing responses: {str(e)}"])
    
    def _clean_answer(self, answer: str) -> str:
        """Clean and format individual answer"""
        if not answer:
            return "No answer available."
        
        # Remove extra whitespace
        cleaned = ' '.join(answer.split())
        
        # Ensure proper sentence ending
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        return cleaned
    
    def build_detailed_response(
        self, 
        answers: List[str], 
        sources: List[str] = None,
        confidence_scores: List[float] = None
    ) -> Dict[str, Any]:
        """Build detailed response with additional metadata"""
        try:
            detailed_response = {
                "answers": answers,
                "metadata": {
                    "total_questions": len(answers),
                    "processed_successfully": len([a for a in answers if not a.startswith("Error")])
                }
            }
            
            if sources:
                detailed_response["sources"] = sources
            
            if confidence_scores:
                detailed_response["confidence_scores"] = confidence_scores
            
            return detailed_response
            
        except Exception as e:
            logger.error(f"Error building detailed response: {str(e)}")
            return {"answers": answers, "error": str(e)}