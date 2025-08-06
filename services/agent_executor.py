# # services/agent_executor.py
# from typing import List
# from langchain.agents import AgentExecutor, create_structured_chat_agent
# from langchain.tools import Tool
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.memory import ConversationBufferMemory
# from loguru import logger
# from langchain import hub # NEW: Import the LangChain Hub

# from core.config import settings
# from services.vector_store import VectorStoreManager
# from services.clause_matcher import ClauseMatcher

# class RAGAgentExecutor:
#     def __init__(self, vector_store: VectorStoreManager):
#         self.vector_store = vector_store
#         self.clause_matcher = ClauseMatcher()
#         self.llm = ChatGoogleGenerativeAI(
#             model=settings.GOOGLE_GEMINI_MODEL_NAME,
#             google_api_key=settings.GOOGLE_API_KEY,
#             temperature=0.1,
#             convert_system_message_to_human=True
#         )
#         self.memory = ConversationBufferMemory(
#             memory_key="chat_history",
#             return_messages=True
#         )
#         self.tools = self._create_tools()
#         self.agent_executor = self._create_agent_executor()
    
#     def _create_tools(self) -> List[Tool]:
#         """Creates tools for the agent, correctly handling async functions."""
        
#         async def semantic_search_tool(query: str) -> str:
#             """Searches the document for information relevant to the user's query."""
#             try:
#                 results = await self.vector_store.similarity_search_with_score(query, k=5)
#                 if not results:
#                     return "No relevant information found in the document for this query."
#                 formatted_results = [
#                     f"Result {i+1} (Relevance: {score:.2f}):\nContent: {doc.page_content}"
#                     for i, (doc, score) in enumerate(results)
#                 ]
#                 return "\n---\n".join(formatted_results)
#             except Exception as e:
#                 logger.error(f"Error in semantic search tool: {str(e)}")
#                 return f"An error occurred during the search: {str(e)}"

#         def clause_matching_tool(query: str) -> str:
#             """Finds specific clauses by name or number (e.g., 'Clause 4.2', 'Exclusions')."""
#             try:
#                 return self.clause_matcher.find_clause(query)
#             except Exception as e:
#                 return f"Error in clause matching: {str(e)}"
        
#         return [
#             Tool(
#                 name="semantic_document_search",
#                 description="Use this tool to search for general information or answer questions based on the document's content.",
#                 coroutine=semantic_search_tool,
#                 # Provide a placeholder sync function to avoid validation errors
#                 func=lambda q: "This is an async tool." 
#             ),
#             Tool(
#                 name="find_specific_clause",
#                 description="Use this to find a specific clause by number/name when a user asks for it directly.",
#                 func=clause_matching_tool
#             )
#         ]
    
#     def _create_agent_executor(self) -> AgentExecutor:
#         """Creates a functional agent using a compatible constructor and a Hub prompt."""
        
#         # MODIFIED: Instead of manually creating a prompt, we pull the official, tested one
#         # from LangChain Hub. This prompt is specifically designed for structured chat agents
#         # and correctly includes all required variables like {tools} and {agent_scratchpad}.
#         prompt = hub.pull("hwchase17/structured-chat-agent")
        
#         # MODIFIED: Reverting to create_structured_chat_agent, which is compatible
#         # with your version of the Google GenAI library.
#         agent = create_structured_chat_agent(self.llm, self.tools, prompt)

#         return AgentExecutor(
#             agent=agent,
#             tools=self.tools,
#             memory=self.memory,
#             verbose=True,
#             handle_parsing_errors=True,
#             max_iterations=5
#         )
    
#     async def process_question(self, question: str) -> str:
#         """Correctly invokes the agent executor to process the question."""
#         try:
#             logger.info(f"Invoking agent for question: {question}")
            
#             response = await self.agent_executor.ainvoke({
#                 "input": question,
#             })
            
#             return response.get("output", "I encountered an error and could not provide a response.")
            
#         except Exception as e:
#             logger.error(f"Error processing question with agent: {str(e)}")
#             return f"An error occurred while processing your question: {str(e)}"
        
#     # In services/agent_executor.py, inside the RAGAgentExecutor class

#     async def complete_question(self, fragment: str) -> str:
#         """
#         Analyzes user input. If it's a fragment, completes it into a full question.
#         If it's already a full question, it returns it as is.
#         """
#         # Simple check to avoid running the LLM on obviously complete questions
#         if fragment.endswith('?'):
#             return fragment
            
#         logger.info(f"Input is a fragment. Attempting to complete: '{fragment}'")

#         prompt = f"""You are an AI assistant. Your task is to analyze the user's input.
#         - If the input is already a complete, well-formed question, return it exactly as it is.
#         - If the input is an incomplete sentence fragment, complete it into the most likely, specific, and detailed question the user was trying to ask based on the context of an insurance policy.

#         Return ONLY the final, complete question and nothing else.

#         Input: "{fragment}"
#         Completed Question:"""

#         try:
#             # Use the main LLM for the completion task
#             response = await self.llm.ainvoke(prompt)
#             completed_question = response.content.strip()
#             logger.info(f"Completed question: '{completed_question}'")
#             return completed_question
#         except Exception as e:
#             logger.error(f"Could not complete question fragment: {e}")
#             return fragment # Fallback to the original fragment on error


# services/agent_executor.py
from typing import List
import asyncio
import json
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from loguru import logger
from langchain import hub

from core.config import settings
from services.vector_store import VectorStoreManager
from services.clause_matcher import ClauseMatcher

class RAGAgentExecutor:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.clause_matcher = ClauseMatcher()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GOOGLE_GEMINI_MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        # The _create_tools method now builds our specialized toolbox
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent_executor()

    # =================================================================
    # NEW: Specialized Tool Implementations
    # =================================================================

    async def _query_tabular_data_tool(self, query: str) -> str:
        """
        Specialized tool for answering questions about data in tables.
        """
        logger.info(f"Tool engaged: query_tabular_data_tool for query: '{query}'")
        try:
            table_search_query = f"table of benefits schedule policy {query}"
            table_chunks = await self.vector_store.similarity_search(table_search_query, k=3)
            
            if not table_chunks:
                return "Could not find any relevant tables in the document to answer this question."

            table_context = "\n---\n".join([doc.page_content for doc in table_chunks])

            prompt = f"""You are a data analyst. Your task is to answer the user's question based *only* on the following table data.
            If the answer is not in the table, state that clearly.

            Table Data:
            {table_context}

            Question: {query}

            Answer:"""

            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error in Table QA tool: {e}")
            return "An error occurred while querying tabular data."

    async def _find_exclusions_tool(self, query: str) -> str:
        """
        Specialized tool to check if an item or condition is covered by searching for exclusions.
        """
        logger.info(f"Tool engaged: find_exclusions_tool for query: '{query}'")
        try:
            exclusion_search_query = f'{query} exclusion "not covered" limitation "items of personal comfort" "annexure ii"'
            results = await self.vector_store.similarity_search_with_score(exclusion_search_query, k=5)

            if not results:
                return f"No specific exclusions or limitations regarding '{query}' were found. This does not guarantee coverage."

            return "\n---\n".join([f"Result (Relevance: {score:.2f}):\n{doc.page_content}" for doc, score in results])

        except Exception as e:
            logger.error(f"Error in Exclusion Finder tool: {e}")
            return "An error occurred while searching for exclusions."

    async def _semantic_search_tool(self, query: str) -> str:
        """Searches the document for general information, now with entity expansion."""
        logger.info(f"Tool engaged: semantic_search_tool for query: '{query}'")
        try:
            # 1. Entity Expansion Step
            expansion_prompt = f"""You are a query analysis assistant. Look at the following search query and identify if there is a geographic location (like a state or city). If there is, list that location and its primary city in a JSON array. If not, return an empty array.
            Example 1: "Insurance Ombudsman in Gujarat" -> {{"entities": ["Gujarat", "Ahmedabad"]}}
            Example 2: "Maternity benefits" -> {{"entities": []}}
            
            Query: "{query}" """
            
            expanded_query = query
            try:
                response = await self.llm.ainvoke(expansion_prompt)
                # A simple way to extract JSON from the response
                json_response_str = response.content.strip().split("```json\n")[1].split("\n```")[0]
                data = json.loads(json_response_str)
                entities = data.get("entities", [])
                if entities:
                    search_terms = " OR ".join(f'"{e}"' for e in entities)
                    # A robust way to replace the original entity
                    base_query = query.replace(entities[0], "")
                    expanded_query = f"{base_query.strip()} ({search_terms})"
                    logger.info(f"Expanded search query to: '{expanded_query}'")
            except Exception:
                logger.warning("Could not expand entities, using original query.")

            # 2. Perform search with the (potentially expanded) query
            results = await self.vector_store.similarity_search_with_score(expanded_query, k=5)
            
            if not results:
                return "No relevant information found in the document for this query."
            
            formatted_results = [f"Result {i+1} (Relevance: {score:.2f}):\n{doc.page_content}" for doc, score in results]
            return "\n---\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Error in semantic search tool: {e}")
            return f"An error occurred during the search: {str(e)}"

    def _create_tools(self) -> List[Tool]:
        """
        MODIFIED: The agent's toolbox, providing a suite of specialized tools.
        The agent will choose the best tool based on its 'description'.
        """
        return [
            Tool(
                name="query_tabular_data",
                description="Use this for questions about specific plan details, co-payments, coverage limits, or other data likely found in tables.",
                coroutine=self._query_tabular_data_tool,
                func=lambda q: asyncio.run(self._query_tabular_data_tool(q))
            ),
            Tool(
                name="find_policy_exclusions",
                description="Use this to check if a specific item, service, or condition is explicitly NOT covered or has limitations. Best for questions like 'Is X covered?'.",
                coroutine=self._find_exclusions_tool,
                func=lambda q: asyncio.run(self._find_exclusions_tool(q))
            ),
            Tool(
                name="general_semantic_search",
                description="Use this as a general-purpose search for any information that doesn't fit the other specialized tools, especially for finding contact details or addresses.",
                coroutine=self._semantic_search_tool,
                func=lambda q: asyncio.run(self._semantic_search_tool(q))
            )
        ]
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Creates the agent using the official LangChain Hub prompt."""
        prompt = hub.pull("hwchase17/structured-chat-agent")
        agent = create_structured_chat_agent(self.llm, self.tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )

    async def complete_question(self, fragment: str) -> str:
        """Analyzes and completes user input if it's a fragment."""
        if '?' in fragment or len(fragment.split()) > 10: # Simple checks for completeness
            return fragment
            
        logger.info(f"Input is a fragment. Attempting to complete: '{fragment}'")
        prompt = f"""You are an AI assistant. Your task is to analyze the user's input.
        - If the input is already a complete, well-formed question, return it exactly as it is.
        - If it is an incomplete sentence fragment, complete it into the most likely, specific, and detailed question the user was trying to ask in the context of an insurance policy.
        Return ONLY the final, complete question and nothing else.
        Input: "{fragment}"
        Completed Question:"""
        try:
            response = await self.llm.ainvoke(prompt)
            completed_question = response.content.strip()
            logger.info(f"Completed question: '{completed_question}'")
            return completed_question
        except Exception as e:
            logger.error(f"Could not complete question fragment: {e}")
            return fragment

    async def process_question(self, question: str) -> str:
        """Invokes the agent to process a question."""
        try:
            logger.info(f"Invoking agent for question: {question}")
            response = await self.agent_executor.ainvoke({
                "input": question,
                "chat_history": self.memory.chat_memory.messages
            })
            return response.get("output", "I encountered an error and could not provide a response.")
        except Exception as e:
            logger.error(f"Error processing question with agent: {str(e)}")
            return f"An error occurred while processing your question: {str(e)}"