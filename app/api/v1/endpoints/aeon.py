"""
AEON AI twin endpoints - Phase 1 and Phase 2 capabilities
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database import get_db
from app.models.aeon import (
    ChatRequest, ChatResponse, ConversationResponse, MemoryEntryCreate,
    MemoryEntryResponse, AEONStatus, ChatMessageResponse
)
from app.services.aeon_service import AEONService
from app.core.security import get_current_active_user
from app.database.models import User

router = APIRouter()
logger = get_logger(__name__)


@router.get("/status", response_model=AEONStatus)
async def get_aeon_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AEON status and statistics"""
    try:
        aeon_status = AEONService.get_aeon_status(db, current_user.id)
        return aeon_status
    except Exception as e:
        logger.error(f"Error getting AEON status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AEON status"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_aeon(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Chat with AEON"""
    try:
        response = AEONService.chat_with_aeon(db, current_user.id, chat_request)
        logger.info(f"Chat completed for user {current_user.username}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat failed"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's conversations"""
    try:
        conversations = AEONService.get_user_conversations(db, current_user.id, skip, limit)
        return [ConversationResponse.model_validate(conv) for conv in conversations]
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific conversation with messages"""
    try:
        conversation = AEONService.get_conversation(db, conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get messages for this conversation
        messages = AEONService.get_conversation_messages(db, conversation_id)
        conversation_response = ConversationResponse.model_validate(conversation)
        conversation_response.messages = [ChatMessageResponse.model_validate(msg) for msg in messages]
        
        return conversation_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )


@router.post("/memories", response_model=MemoryEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_data: MemoryEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new memory entry"""
    try:
        memory = AEONService.create_memory_entry(db, current_user.id, memory_data)
        return MemoryEntryResponse.model_validate(memory)
    except Exception as e:
        logger.error(f"Error creating memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create memory"
        )


@router.get("/memories", response_model=List[MemoryEntryResponse])
async def get_memories(
    memory_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's memories"""
    try:
        memories = AEONService.get_user_memories(db, current_user.id, memory_type)
        return [MemoryEntryResponse.model_validate(memory) for memory in memories]
    except Exception as e:
        logger.error(f"Error getting memories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get memories"
        )


# Phase 2 Enhanced Endpoints
@router.post("/chat/enhanced", response_model=ChatResponse)
async def chat_with_aeon_enhanced(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Chat with AEON using Phase 2 RAG capabilities"""
    try:
        from app.services.enhanced_aeon_service import get_enhanced_aeon_service
        
        enhanced_service = await get_enhanced_aeon_service()
        response = await enhanced_service.chat_with_aeon_enhanced(db, current_user.id, chat_request)
        logger.info(f"Enhanced chat completed for user {current_user.username}")
        return response
    except Exception as e:
        logger.error(f"Enhanced chat failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Enhanced chat service temporarily unavailable"
        )


@router.get("/status/enhanced")
async def get_enhanced_aeon_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get enhanced AEON status with Phase 2 hybrid memory system info"""
    try:
        from app.services.enhanced_aeon_service import get_enhanced_aeon_service
        
        enhanced_service = await get_enhanced_aeon_service()
        status_info = await enhanced_service.get_enhanced_aeon_status(db, current_user.id)
        return status_info
    except Exception as e:
        logger.error(f"Enhanced status retrieval failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Enhanced status service temporarily unavailable"
        )


@router.post("/memories/enhanced")
async def create_memory_enhanced(
    memory_data: MemoryEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create memory with Phase 2 vector and graph storage"""
    try:
        from app.services.enhanced_aeon_service import get_enhanced_aeon_service
        
        enhanced_service = await get_enhanced_aeon_service()
        result = await enhanced_service.create_memory_entry_enhanced(
            db, current_user.id, memory_data
        )
        return result
    except Exception as e:
        logger.error(f"Enhanced memory creation failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Enhanced memory creation failed"
        )


@router.get("/memories/search")
async def search_memories(
    query: str = Query(..., description="Search query for memories"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    min_importance: int = Query(1, description="Minimum importance level"),
    limit: int = Query(10, description="Maximum number of results"),
    enhanced: bool = Query(False, description="Use Phase 2 enhanced search"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search memories using traditional or enhanced Phase 2 methods"""
    try:
        if enhanced:
            from app.services.enhanced_aeon_service import get_enhanced_aeon_service
            
            enhanced_service = await get_enhanced_aeon_service()
            results = await enhanced_service.search_memories_enhanced(
                db, current_user.id, query, memory_type, min_importance, limit
            )
            return results
        else:
            # Traditional search (Phase 1)
            memories = AEONService.get_user_memories(db, current_user.id, memory_type)
            # Simple text filtering for traditional search
            filtered_memories = []
            query_lower = query.lower()
            for memory in memories:
                if (query_lower in memory.content.lower() and 
                    memory.importance >= min_importance):
                    filtered_memories.append(memory)
            
            return {
                "query": query,
                "method": "traditional",
                "results": [MemoryEntryResponse.model_validate(m) for m in filtered_memories[:limit]]
            }
    except Exception as e:
        logger.error(f"Memory search failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory search failed"
        )


@router.post("/graph/initialize")
async def initialize_user_graph(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initialize user in the Phase 2 graph database"""
    try:
        from app.services.enhanced_aeon_service import get_enhanced_aeon_service
        
        enhanced_service = await get_enhanced_aeon_service()
        result = await enhanced_service.initialize_user_graph(db, current_user.id)
        return result
    except Exception as e:
        logger.error(f"Graph initialization failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Graph initialization failed"
        )


@router.get("/context/retrieve")
async def retrieve_context(
    query: str = Query(..., description="Query to retrieve relevant context"),
    max_memories: int = Query(5, description="Maximum memories to retrieve"),
    include_graph: bool = Query(True, description="Include graph relationships"),
    conversation_id: Optional[int] = Query(None, description="Exclude this conversation"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve relevant context using Phase 2 RAG system"""
    try:
        from app.services.rag_service import get_rag_service
        
        rag_service = await get_rag_service()
        context_data = await rag_service.retrieve_relevant_context(
            user_id=current_user.id,
            query=query,
            conversation_id=conversation_id,
            max_memories=max_memories,
            include_graph_context=include_graph
        )
        return context_data
    except Exception as e:
        logger.error(f"Context retrieval failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Context retrieval failed"
        )


@router.get("/health/hybrid")
async def get_hybrid_system_health():
    """Get health status of the Phase 2 hybrid memory system"""
    try:
        from app.services.database import check_database_health
        
        health_status = await check_database_health()
        return health_status
    except Exception as e:
        logger.error(f"Hybrid system health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        ) 