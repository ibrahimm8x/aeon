"""
Enhanced AEON service layer for Phase 2 with RAG capabilities
Extends the original AEON service with hybrid memory system and intelligent context retrieval
"""

import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database.models import User, Conversation, ChatMessage, MemoryEntry
from app.models.aeon import (
    ChatRequest, ChatResponse, ChatMessageCreate, ChatMessageResponse, ConversationResponse,
    MemoryEntryCreate, AEONStatus, MessageRole, MessageType
)
from app.core.config import settings
from app.core.logging import get_logger
from app.services.aeon_service import AEONService
from app.services.rag_service import get_rag_service
from app.services.vector_service import get_vector_service
from app.services.graph_service import get_graph_service

logger = get_logger(__name__)


class EnhancedAEONService(AEONService):
    """Enhanced AEON service with Phase 2 RAG capabilities"""
    
    @staticmethod
    async def chat_with_aeon_enhanced(db: Session, user_id: int, chat_request: ChatRequest) -> ChatResponse:
        """Enhanced chat function with RAG-powered memory retrieval"""
        start_time = time.time()
        
        try:
            # Get or create conversation
            conversation_id = chat_request.conversation_id
            if not conversation_id:
                conversation = AEONService.create_conversation(db, user_id)
                conversation_id = conversation.id
            
            # Verify conversation belongs to user
            conversation = AEONService.get_conversation(db, conversation_id, user_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            # Add user message to database
            user_message = AEONService.add_message_to_conversation(
                db, conversation_id, user_id, chat_request.message, MessageRole.USER
            )
            
            # Get conversation history for context
            messages = AEONService.get_conversation_messages(db, conversation_id, limit=20)
            conversation_history = []
            
            for msg in messages[-10:]:  # Last 10 messages
                role = "user" if msg.role == "user" else "assistant"
                conversation_history.append({
                    "role": role,
                    "content": msg.content
                })
            
            # Generate enhanced response using RAG
            rag_service = await get_rag_service()
            response_data = await rag_service.generate_enhanced_response(
                user_id=user_id,
                user_message=chat_request.message,
                conversation_history=conversation_history,
                conversation_id=conversation_id
            )
            
            aeon_response_content = response_data["response"]
            
            # Add AEON response to database
            aeon_message = AEONService.add_message_to_conversation(
                db, conversation_id, user_id, aeon_response_content, MessageRole.AEON
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Convert to response models
            aeon_message_response = ChatMessageResponse.model_validate(aeon_message)
            
            # Build enhanced response with metadata
            enhanced_response = ChatResponse(
                message=aeon_message_response,
                conversation_id=conversation_id,
                response_time=response_time
            )
            
            # Add RAG metadata to response
            if hasattr(enhanced_response, '__dict__'):
                enhanced_response.__dict__.update({
                    "context_sources": response_data.get("context_used", {}),
                    "memories_referenced": response_data.get("memories_referenced", 0),
                    "ai_tokens_used": response_data.get("tokens_used", 0)
                })
            
            logger.info(f"Enhanced chat response generated in {response_time:.2f}s with {response_data.get('memories_referenced', 0)} memories")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Enhanced chat failed: {str(e)}")
            # Fallback to original chat method
            return await EnhancedAEONService._fallback_chat(db, user_id, chat_request, start_time)
    
    @staticmethod
    async def create_memory_entry_enhanced(
        db: Session, 
        user_id: int, 
        memory_data: MemoryEntryCreate
    ) -> Dict[str, Any]:
        """Enhanced memory creation with vector and graph storage"""
        try:
            # Create memory in traditional database
            memory = AEONService.create_memory_entry(db, user_id, memory_data)
            
            # Store in hybrid memory system
            rag_service = await get_rag_service()
            rag_result = await rag_service.store_memory_with_context(
                user_id=user_id,
                content=memory_data.content,
                memory_type=memory_data.memory_type,
                importance=memory_data.importance,
                metadata=memory_data.metadata
            )
            
            # Create user node in graph if it doesn't exist
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                graph_service = await get_graph_service()
                await graph_service.create_user_node(
                    user_id=user_id,
                    username=user.username,
                    email=user.email
                )
            
            logger.info(f"Enhanced memory created: {memory.id} -> {rag_result['memory_id']}")
            
            return {
                "memory": memory,
                "vector_id": rag_result.get("memory_id"),
                "concepts_extracted": rag_result.get("concepts_extracted", 0),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Enhanced memory creation failed: {str(e)}")
            # Fallback to original method
            memory = AEONService.create_memory_entry(db, user_id, memory_data)
            return {
                "memory": memory,
                "vector_id": None,
                "concepts_extracted": 0,
                "status": "fallback",
                "error": str(e)
            }
    
    @staticmethod
    async def get_enhanced_aeon_status(db: Session, user_id: int) -> Dict[str, Any]:
        """Get enhanced AEON status with hybrid memory system info"""
        try:
            # Get basic status
            basic_status = AEONService.get_aeon_status(db, user_id)
            
            # Get vector database info
            vector_service = await get_vector_service()
            vector_health = await vector_service.get_health_status()
            
            # Get graph database info
            graph_service = await get_graph_service()
            graph_health = await graph_service.get_health_status()
            knowledge_graph = await graph_service.get_user_knowledge_graph(user_id)
            
            # Build enhanced status
            enhanced_status = {
                "basic_status": basic_status.__dict__,
                "hybrid_memory": {
                    "vector_db": {
                        "status": vector_health.get("status", "unknown"),
                        "memory_count": vector_health.get("memory_count", 0),
                        "conversation_count": vector_health.get("conversation_count", 0)
                    },
                    "graph_db": {
                        "status": graph_health.get("status", "unknown"),
                        "total_nodes": graph_health.get("total_nodes", 0),
                        "knowledge_graph": knowledge_graph
                    }
                },
                "capabilities": {
                    "rag_enabled": True,
                    "hybrid_memory": True,
                    "concept_extraction": True,
                    "memory_relationships": True
                }
            }
            
            return enhanced_status
            
        except Exception as e:
            logger.error(f"Enhanced status retrieval failed: {str(e)}")
            # Fallback to basic status
            basic_status = AEONService.get_aeon_status(db, user_id)
            return {
                "basic_status": basic_status.__dict__,
                "hybrid_memory": {"error": str(e)},
                "capabilities": {"rag_enabled": False}
            }
    
    @staticmethod
    async def search_memories_enhanced(
        db: Session,
        user_id: int,
        query: str,
        memory_type: Optional[str] = None,
        min_importance: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Enhanced memory search using hybrid vector and graph approach"""
        try:
            # Get traditional database memories
            traditional_memories = AEONService.get_user_memories(db, user_id, memory_type)
            
            # Get RAG-powered search results
            rag_service = await get_rag_service()
            context_data = await rag_service.retrieve_relevant_context(
                user_id=user_id,
                query=query,
                max_memories=limit,
                include_graph_context=True
            )
            
            return {
                "query": query,
                "traditional_results": len(traditional_memories),
                "rag_results": context_data,
                "combined_insights": await EnhancedAEONService._combine_search_results(
                    traditional_memories, context_data["memory_details"]
                )
            }
            
        except Exception as e:
            logger.error(f"Enhanced memory search failed: {str(e)}")
            # Fallback to traditional search
            traditional_memories = AEONService.get_user_memories(db, user_id, memory_type)
            return {
                "query": query,
                "traditional_results": len(traditional_memories),
                "memories": traditional_memories[:limit],
                "error": str(e)
            }
    
    @staticmethod
    async def initialize_user_graph(db: Session, user_id: int) -> Dict[str, Any]:
        """Initialize user in the graph database"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            graph_service = await get_graph_service()
            await graph_service.create_user_node(
                user_id=user_id,
                username=user.username,
                email=user.email,
                metadata={
                    "full_name": user.full_name,
                    "bio": user.bio,
                    "role": user.role
                }
            )
            
            # Create conversation nodes for existing conversations
            conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
            for conv in conversations:
                await graph_service.create_conversation_node(
                    conversation_id=conv.id,
                    user_id=user_id,
                    title=conv.title
                )
            
            logger.info(f"User graph initialized for user {user_id}")
            return {
                "status": "success",
                "user_node_created": True,
                "conversations_migrated": len(conversations)
            }
            
        except Exception as e:
            logger.error(f"User graph initialization failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    async def _fallback_chat(db: Session, user_id: int, chat_request: ChatRequest, start_time: float) -> ChatResponse:
        """Fallback to original chat method if enhanced fails"""
        try:
            logger.warning("Using fallback chat method")
            return AEONService.chat_with_aeon(db, user_id, chat_request)
        except Exception as e:
            logger.error(f"Fallback chat also failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Chat service temporarily unavailable"
            )
    
    @staticmethod
    async def _combine_search_results(traditional_memories: List, rag_memories: List[Dict]) -> List[Dict]:
        """Combine traditional and RAG search results"""
        combined = []
        seen_content = set()
        
        # Add RAG results first (they have relevance scores)
        for rag_mem in rag_memories:
            content = rag_mem.get("content", "")
            if content not in seen_content:
                combined.append({
                    "content": content,
                    "source": "rag",
                    "relevance_score": rag_mem.get("relevance_score", 0),
                    "memory_type": rag_mem.get("memory_type", "unknown"),
                    "importance": rag_mem.get("importance", 0)
                })
                seen_content.add(content)
        
        # Add traditional results if not already included
        for trad_mem in traditional_memories:
            content = trad_mem.content
            if content not in seen_content:
                combined.append({
                    "content": content,
                    "source": "traditional",
                    "memory_type": trad_mem.memory_type,
                    "importance": trad_mem.importance,
                    "created_at": trad_mem.created_at.isoformat()
                })
                seen_content.add(content)
        
        return combined


# Global enhanced service instance
enhanced_aeon_service = EnhancedAEONService()


async def get_enhanced_aeon_service() -> EnhancedAEONService:
    """Get the global enhanced AEON service instance"""
    return enhanced_aeon_service 