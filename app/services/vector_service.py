"""
Vector database service using ChromaDB for AEON Phase 2
Handles vector storage, retrieval, and similarity search for memories and conversations
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorService:
    """Vector database service for memory and conversation storage"""
    
    def __init__(self):
        self.client = None
        self.embedding_function = None
        self.memory_collection = None
        self.conversation_collection = None
        self._sentence_transformer = None
        
    async def initialize(self):
        """Initialize ChromaDB client and collections"""
        try:
            # Initialize ChromaDB client using persistent client to avoid tenant issues
            self.client = chromadb.PersistentClient(
                path="/tmp/chroma_aeon",
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            # Initialize embedding function using OpenAI
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=settings.openai_embedding_model
            )
            
            # Initialize sentence transformer for backup embeddings
            self._sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create or get collections
            await self._setup_collections()
            
            logger.info("Vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {str(e)}")
            raise
    
    async def _setup_collections(self):
        """Setup ChromaDB collections for memories and conversations"""
        try:
            # Memory collection for storing user memories as vectors
            self.memory_collection = self.client.get_or_create_collection(
                name="aeon_memories",
                embedding_function=self.embedding_function,
                metadata={"description": "AEON user memories with vector embeddings"}
            )
            
            # Conversation collection for storing conversation chunks
            self.conversation_collection = self.client.get_or_create_collection(
                name="aeon_conversations",
                embedding_function=self.embedding_function,
                metadata={"description": "AEON conversation history with vector embeddings"}
            )
            
            logger.info("ChromaDB collections setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup ChromaDB collections: {str(e)}")
            raise
    
    async def store_memory(
        self, 
        user_id: int, 
        content: str, 
        memory_type: str, 
        importance: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a memory in the vector database"""
        try:
            # Generate unique ID for the memory
            memory_id = f"memory_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Prepare metadata
            memory_metadata = {
                "user_id": user_id,
                "memory_type": memory_type,
                "importance": importance,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store in ChromaDB
            self.memory_collection.add(
                documents=[content],
                ids=[memory_id],
                metadatas=[memory_metadata]
            )
            
            logger.info(f"Memory stored in vector DB: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory in vector DB: {str(e)}")
            raise
    
    async def store_conversation_chunk(
        self,
        user_id: int,
        conversation_id: int,
        content: str,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a conversation chunk in the vector database"""
        try:
            # Generate unique ID for the chunk
            chunk_id = f"conv_{conversation_id}_chunk_{chunk_index}_{uuid.uuid4().hex[:8]}"
            
            # Prepare metadata
            chunk_metadata = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "chunk_index": chunk_index,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store in ChromaDB
            self.conversation_collection.add(
                documents=[content],
                ids=[chunk_id],
                metadatas=[chunk_metadata]
            )
            
            logger.info(f"Conversation chunk stored: {chunk_id}")
            return chunk_id
            
        except Exception as e:
            logger.error(f"Failed to store conversation chunk: {str(e)}")
            raise
    
    async def search_relevant_memories(
        self,
        user_id: int,
        query: str,
        limit: int = 5,
        min_importance: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories using vector similarity"""
        try:
            # Query the memory collection
            results = self.memory_collection.query(
                query_texts=[query],
                n_results=limit * 2,  # Get more results to filter by user and importance
                where={"user_id": user_id, "importance": {"$gte": min_importance}}
            )
            
            # Process results
            relevant_memories = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    
                    relevant_memories.append({
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1 - distance,  # Convert distance to similarity
                        "memory_type": metadata.get("memory_type", "unknown"),
                        "importance": metadata.get("importance", 0)
                    })
            
            # Sort by relevance and importance
            relevant_memories.sort(
                key=lambda x: (x["relevance_score"] * 0.7 + x["importance"] * 0.03),
                reverse=True
            )
            
            logger.info(f"Found {len(relevant_memories)} relevant memories for user {user_id}")
            return relevant_memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            return []
    
    async def search_conversation_context(
        self,
        user_id: int,
        query: str,
        exclude_conversation_id: Optional[int] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for relevant conversation context"""
        try:
            # Build where clause
            where_clause = {"user_id": user_id}
            if exclude_conversation_id:
                where_clause["conversation_id"] = {"$ne": exclude_conversation_id}
            
            # Query the conversation collection
            results = self.conversation_collection.query(
                query_texts=[query],
                n_results=limit * 2,
                where=where_clause
            )
            
            # Process results
            relevant_context = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    
                    relevant_context.append({
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1 - distance,
                        "conversation_id": metadata.get("conversation_id")
                    })
            
            # Sort by relevance
            relevant_context.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            logger.info(f"Found {len(relevant_context)} relevant conversation contexts")
            return relevant_context[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search conversation context: {str(e)}")
            return []
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Check the health of the vector service"""
        try:
            # Test connection by getting collection count
            collections = self.client.list_collections()
            
            # Get collection stats
            memory_count = self.memory_collection.count() if self.memory_collection else 0
            conversation_count = self.conversation_collection.count() if self.conversation_collection else 0
            
            return {
                "status": "healthy",
                "collections": len(collections),
                "memory_count": memory_count,
                "conversation_count": conversation_count,
                "client_connected": True
            }
            
        except Exception as e:
            logger.error(f"Vector service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "client_connected": False
            }
    
    async def close(self):
        """Clean up resources"""
        try:
            if self.client:
                # ChromaDB client doesn't need explicit closing
                pass
            logger.info("Vector service closed")
        except Exception as e:
            logger.error(f"Error closing vector service: {str(e)}")


# Global vector service instance
vector_service = VectorService()


async def get_vector_service() -> VectorService:
    """Get the global vector service instance"""
    if not vector_service.client:
        await vector_service.initialize()
    return vector_service 