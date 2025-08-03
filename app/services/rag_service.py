"""
RAG (Retrieval-Augmented Generation) service for AEON Phase 2
Combines vector similarity search and graph relationships for enhanced memory retrieval
"""

import re
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import tiktoken
from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.services.vector_service import get_vector_service
from app.services.graph_service import get_graph_service

logger = get_logger(__name__)


class RAGService:
    """RAG service for intelligent memory retrieval and context enhancement"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        self.max_context_tokens = 3000  # Reserve tokens for context
        
    async def store_memory_with_context(
        self,
        user_id: int,
        content: str,
        memory_type: str,
        importance: int,
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Store a memory in both vector and graph databases with extracted context"""
        try:
            vector_service = await get_vector_service()
            graph_service = await get_graph_service()
            
            # Store in vector database
            memory_id = await vector_service.store_memory(
                user_id=user_id,
                content=content,
                memory_type=memory_type,
                importance=importance,
                metadata=metadata
            )
            
            # Store in graph database
            await graph_service.create_memory_node(
                memory_id=memory_id,
                user_id=user_id,
                content=content,
                memory_type=memory_type,
                importance=importance,
                metadata=metadata
            )
            
            # Extract and link concepts
            concepts = await self._extract_concepts(content)
            if concepts:
                await graph_service.extract_and_link_concepts(
                    memory_id=memory_id,
                    content=content,
                    concepts=concepts
                )
            
            # Find and create relationships with existing memories
            await self._create_memory_relationships(user_id, memory_id, content)
            
            logger.info(f"Memory stored with context: {memory_id}")
            return {"memory_id": memory_id, "concepts_extracted": len(concepts)}
            
        except Exception as e:
            logger.error(f"Failed to store memory with context: {str(e)}")
            raise
    
    async def retrieve_relevant_context(
        self,
        user_id: int,
        query: str,
        conversation_id: Optional[int] = None,
        max_memories: int = 5,
        include_graph_context: bool = True
    ) -> Dict[str, Any]:
        """Retrieve relevant memories and context using hybrid approach"""
        try:
            vector_service = await get_vector_service()
            graph_service = await get_graph_service()
            
            # 1. Vector similarity search for memories
            vector_memories = await vector_service.search_relevant_memories(
                user_id=user_id,
                query=query,
                limit=max_memories,
                min_importance=3
            )
            
            # 2. Search conversation history for context
            conversation_context = await vector_service.search_conversation_context(
                user_id=user_id,
                query=query,
                exclude_conversation_id=conversation_id,
                limit=3
            )
            
            # 3. Get graph-based relationships if enabled
            graph_memories = []
            if include_graph_context and vector_memories:
                for memory in vector_memories[:2]:  # Use top 2 memories to find related ones
                    memory_id = memory.get("metadata", {}).get("memory_id")
                    if memory_id:
                        related = await graph_service.find_related_memories(
                            memory_id=memory_id,
                            max_depth=2,
                            limit=3
                        )
                        graph_memories.extend(related)
            
            # 4. Combine and deduplicate results
            combined_context = await self._combine_context_sources(
                vector_memories=vector_memories,
                conversation_context=conversation_context,
                graph_memories=graph_memories
            )
            
            # 5. Build context string with token management
            context_string = await self._build_context_string(combined_context)
            
            return {
                "context": context_string,
                "sources": {
                    "vector_memories": len(vector_memories),
                    "conversation_context": len(conversation_context),
                    "graph_memories": len(graph_memories)
                },
                "memory_details": combined_context
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {str(e)}")
            return {"context": "", "sources": {}, "memory_details": []}
    
    async def generate_enhanced_response(
        self,
        user_id: int,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate AI response enhanced with RAG context"""
        try:
            # Retrieve relevant context
            context_data = await self.retrieve_relevant_context(
                user_id=user_id,
                query=user_message,
                conversation_id=conversation_id,
                max_memories=5
            )
            
            # Build enhanced system message
            system_message = await self._build_enhanced_system_message(
                user_id=user_id,
                context=context_data["context"]
            )
            
            # Prepare messages for OpenAI
            messages = [system_message]
            
            # Add conversation history (limited by tokens)
            history_tokens = 0
            for msg in conversation_history[-10:]:  # Last 10 messages max
                msg_tokens = len(self.encoding.encode(msg["content"]))
                if history_tokens + msg_tokens > 1000:  # Reserve 1000 tokens for history
                    break
                messages.append(msg)
                history_tokens += msg_tokens
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=600,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            aeon_response = response.choices[0].message.content.strip()
            
            # Store conversation chunk for future retrieval
            await self._store_conversation_chunk(
                user_id=user_id,
                conversation_id=conversation_id or 0,
                content=f"User: {user_message}\nAEON: {aeon_response}"
            )
            
            # Extract and store any new memories from the conversation
            await self._extract_conversation_memories(
                user_id=user_id,
                user_message=user_message,
                aeon_response=aeon_response
            )
            
            return {
                "response": aeon_response,
                "context_used": context_data["sources"],
                "memories_referenced": len(context_data["memory_details"]),
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced response: {str(e)}")
            return {
                "response": "I'm having trouble accessing my memories right now. Could you try again?",
                "context_used": {},
                "memories_referenced": 0,
                "tokens_used": 0
            }
    
    async def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content using NLP"""
        try:
            # Use OpenAI to extract concepts
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract 3-5 key concepts or topics from the following text. Return only the concepts separated by commas, no explanations."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            concepts_text = response.choices[0].message.content.strip()
            concepts = [c.strip().lower() for c in concepts_text.split(",") if c.strip()]
            
            return concepts[:5]  # Limit to 5 concepts
            
        except Exception as e:
            logger.error(f"Failed to extract concepts: {str(e)}")
            # Fallback: simple keyword extraction
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            return list(set(words))[:5]
    
    async def _create_memory_relationships(self, user_id: int, memory_id: str, content: str):
        """Create relationships between memories based on similarity"""
        try:
            vector_service = await get_vector_service()
            graph_service = await get_graph_service()
            
            # Find similar memories
            similar_memories = await vector_service.search_relevant_memories(
                user_id=user_id,
                query=content,
                limit=3,
                min_importance=1
            )
            
            # Create relationships in graph
            for similar in similar_memories:
                similar_id = similar.get("metadata", {}).get("memory_id")
                if similar_id and similar_id != memory_id:
                    relevance = similar.get("relevance_score", 0)
                    if relevance > 0.7:  # High similarity threshold
                        await graph_service.create_memory_relationship(
                            memory_id1=memory_id,
                            memory_id2=similar_id,
                            relationship_type="similar",
                            strength=relevance
                        )
            
        except Exception as e:
            logger.error(f"Failed to create memory relationships: {str(e)}")
    
    async def _combine_context_sources(
        self,
        vector_memories: List[Dict],
        conversation_context: List[Dict],
        graph_memories: List[Dict]
    ) -> List[Dict]:
        """Combine and deduplicate context from different sources"""
        combined = []
        seen_content = set()
        
        # Prioritize vector memories (highest relevance)
        for memory in vector_memories:
            content = memory.get("content", "")
            if content not in seen_content:
                memory["source"] = "vector"
                combined.append(memory)
                seen_content.add(content)
        
        # Add graph memories (relationships)
        for memory in graph_memories:
            content = memory.get("content", "")
            if content not in seen_content:
                memory["source"] = "graph"
                combined.append(memory)
                seen_content.add(content)
        
        # Add conversation context
        for context in conversation_context:
            content = context.get("content", "")
            if content not in seen_content:
                context["source"] = "conversation"
                combined.append(context)
                seen_content.add(content)
        
        return combined
    
    async def _build_context_string(self, context_items: List[Dict]) -> str:
        """Build a context string from memory items with token management"""
        context_parts = []
        total_tokens = 0
        
        for item in context_items:
            content = item.get("content", "")
            source = item.get("source", "unknown")
            importance = item.get("importance", 0)
            
            # Format context item
            if source == "conversation":
                formatted = f"[Previous conversation]: {content}"
            else:
                formatted = f"[Memory - {source}, importance: {importance}]: {content}"
            
            # Check token count
            item_tokens = len(self.encoding.encode(formatted))
            if total_tokens + item_tokens > self.max_context_tokens:
                break
                
            context_parts.append(formatted)
            total_tokens += item_tokens
        
        return "\n\n".join(context_parts)
    
    async def _build_enhanced_system_message(self, user_id: int, context: str) -> Dict[str, str]:
        """Build an enhanced system message with context"""
        graph_service = await get_graph_service()
        
        # Get user knowledge graph summary
        kg_summary = await graph_service.get_user_knowledge_graph(user_id)
        
        system_content = f"""You are AEON, a digital AI twin with perfect memory and deep understanding of your owner.

MEMORY CONTEXT:
{context}

KNOWLEDGE SUMMARY:
- Memories stored: {kg_summary.get('memory_count', 0)}
- Concepts learned: {kg_summary.get('concept_count', 0)}
- Conversations: {kg_summary.get('conversation_count', 0)}

Use the memory context above to provide personalized, contextual responses. Reference specific memories when relevant, and show that you remember and understand your owner's experiences, preferences, and personality. Always respond as if you're having a natural conversation with someone you know intimately well."""
        
        return {
            "role": "system",
            "content": system_content
        }
    
    async def _store_conversation_chunk(self, user_id: int, conversation_id: int, content: str):
        """Store conversation chunk for future retrieval"""
        try:
            vector_service = await get_vector_service()
            
            # Create a chunk index based on current time
            chunk_index = int(datetime.utcnow().timestamp())
            
            await vector_service.store_conversation_chunk(
                user_id=user_id,
                conversation_id=conversation_id,
                content=content,
                chunk_index=chunk_index,
                metadata={"stored_at": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            logger.error(f"Failed to store conversation chunk: {str(e)}")
    
    async def _extract_conversation_memories(self, user_id: int, user_message: str, aeon_response: str):
        """Extract important memories from conversation"""
        try:
            # Use OpenAI to determine if conversation contains memorable information
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the conversation and determine if it contains information worth remembering long-term. 
                        Return "YES" if it contains personal preferences, important facts, experiences, or meaningful information about the user.
                        Return "NO" if it's just casual chat or temporary information.
                        Then provide a brief memory summary if YES."""
                    },
                    {
                        "role": "user",
                        "content": f"User: {user_message}\nAEON: {aeon_response}"
                    }
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content.strip()
            
            if analysis.startswith("YES"):
                # Extract memory content
                memory_content = analysis.replace("YES", "").strip()
                if memory_content:
                    # Store as a memory
                    await self.store_memory_with_context(
                        user_id=user_id,
                        content=memory_content,
                        memory_type="conversation_extract",
                        importance=5,  # Medium importance for conversation extracts
                        metadata={"extracted_from": "conversation"}
                    )
            
        except Exception as e:
            logger.error(f"Failed to extract conversation memories: {str(e)}")


# Global RAG service instance
rag_service = RAGService()


async def get_rag_service() -> RAGService:
    """Get the global RAG service instance"""
    return rag_service 