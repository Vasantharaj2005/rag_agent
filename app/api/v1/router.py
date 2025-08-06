# api/v1/routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger
import asyncio # NEW: Import asyncio for concurrent processing
import traceback

from models.request_response import RAGRequest, RAGResponse
from services.document_loader import DocumentLoader
from services.vector_store import VectorStoreManager
from services.agent_executor import RAGAgentExecutor
from services.response_builder import ResponseBuilder

router = APIRouter()

@router.post("/hackrx/run", response_model=RAGResponse)
async def run_rag_pipeline(request: RAGRequest, background_tasks: BackgroundTasks):
    """
    MODIFIED: High-performance RAG pipeline that completes question fragments
    and processes all questions concurrently.
    """
    try:
        logger.info(f"Processing RAG request with {len(request.questions)} questions")
        
        # Steps 1, 2, and 3 remain sequential as they are prerequisites
        logger.info("Step 1: Loading and processing document...")
        document_loader = DocumentLoader()
        documents = await document_loader.load_from_url(str(request.documents))
        
        logger.info("Step 2: Creating embeddings and storing in vector database...")
        vector_store = VectorStoreManager()
        await vector_store.initialize()
        doc_ids = await vector_store.add_documents(documents)
        
        logger.info("Step 3: Initializing agent executor...")
        agent_executor = RAGAgentExecutor(vector_store)
        
        # MODIFIED: Step 4 now runs all questions in parallel for maximum speed
        logger.info("Step 4: Processing questions concurrently through agent...")
        
        async def process_single_question(question: str, index: int):
            """Helper function to manage the completion and processing of one question."""
            logger.info(f"Starting pipeline for question {index}/{len(request.questions)}...")
            try:
                # NEW: First, complete the question if it's a fragment
                completed_question = await agent_executor.complete_question(question)
                if completed_question != question:
                    logger.info(f"Completed Q{index}: '{question[:50]}...' -> '{completed_question[:100]}...'")

                # Then, process the now-complete question
                answer = await agent_executor.process_question(completed_question)
                return answer
            except Exception as e:
                logger.error(f"Error processing question {index}: {str(e)}")
                return f"An error occurred while processing this question."

        # Create a list of concurrent tasks
        tasks = [process_single_question(q, i+1) for i, q in enumerate(request.questions)]
        
        # Execute all tasks in parallel and gather the results
        answers = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Step 5: Building structured response...")
        response_builder = ResponseBuilder()
        structured_response = response_builder.build_response(answers)
        
        # Cleanup runs in the background after the response is sent
        background_tasks.add_task(vector_store.cleanup, doc_ids)
        
        logger.info("RAG pipeline completed successfully")
        return structured_response
        
    except Exception as e:
        logger.error(f"RAG pipeline error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )