"""
Graph database service using Neo4j for AEON Phase 2
Handles relationship modeling, knowledge graphs, and complex memory associations
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GraphService:
    """Graph database service for relationships and knowledge modeling"""
    
    def __init__(self):
        self.driver: Optional[Driver] = None
        
    async def initialize(self):
        """Initialize Neo4j driver and setup constraints"""
        try:
            # Create Neo4j driver
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            
            # Verify connectivity
            await self._verify_connectivity()
            
            # Setup database schema
            await self._setup_schema()
            
            logger.info("Graph service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize graph service: {str(e)}")
            raise
    
    async def _verify_connectivity(self):
        """Verify Neo4j connectivity"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record["test"] != 1:
                    raise Exception("Connectivity test failed")
            logger.info("Neo4j connectivity verified")
        except Exception as e:
            logger.error(f"Neo4j connectivity failed: {str(e)}")
            raise
    
    async def _setup_schema(self):
        """Setup Neo4j constraints and indexes"""
        try:
            with self.driver.session() as session:
                # Create constraints
                constraints = [
                    "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
                    "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.memory_id IS UNIQUE",
                    "CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS FOR (c:Conversation) REQUIRE c.conversation_id IS UNIQUE",
                    "CREATE CONSTRAINT concept_name_unique IF NOT EXISTS FOR (con:Concept) REQUIRE con.name IS UNIQUE"
                ]
                
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        # Constraint might already exist
                        logger.debug(f"Constraint creation result: {str(e)}")
                
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX user_created_idx IF NOT EXISTS FOR (u:User) ON (u.created_at)",
                    "CREATE INDEX memory_importance_idx IF NOT EXISTS FOR (m:Memory) ON (m.importance)",
                    "CREATE INDEX memory_type_idx IF NOT EXISTS FOR (m:Memory) ON (m.memory_type)",
                    "CREATE INDEX concept_frequency_idx IF NOT EXISTS FOR (c:Concept) ON (c.frequency)"
                ]
                
                for index in indexes:
                    try:
                        session.run(index)
                    except Exception as e:
                        logger.debug(f"Index creation result: {str(e)}")
                        
            logger.info("Neo4j schema setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup Neo4j schema: {str(e)}")
            raise
    
    async def create_user_node(self, user_id: int, username: str, email: str, metadata: Optional[Dict] = None):
        """Create a user node in the graph"""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (u:User {user_id: $user_id})
                SET u.username = $username,
                    u.email = $email,
                    u.created_at = datetime(),
                    u.updated_at = datetime()
                """
                
                if metadata:
                    for key, value in metadata.items():
                        query += f", u.{key} = ${key}"
                
                query += " RETURN u"
                
                params = {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    **(metadata or {})
                }
                
                result = session.run(query, params)
                record = result.single()
                
                logger.info(f"User node created/updated for user {user_id}")
                return record["u"] if record else None
                
        except Exception as e:
            logger.error(f"Failed to create user node: {str(e)}")
            raise
    
    async def create_memory_node(
        self,
        memory_id: str,
        user_id: int,
        content: str,
        memory_type: str,
        importance: int,
        metadata: Optional[Dict] = None
    ):
        """Create a memory node and link it to the user"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})
                CREATE (m:Memory {
                    memory_id: $memory_id,
                    content: $content,
                    memory_type: $memory_type,
                    importance: $importance,
                    created_at: datetime()
                })
                CREATE (u)-[:HAS_MEMORY]->(m)
                RETURN m
                """
                
                params = {
                    "user_id": user_id,
                    "memory_id": memory_id,
                    "content": content,
                    "memory_type": memory_type,
                    "importance": importance
                }
                
                if metadata:
                    # Add metadata fields to the memory node
                    for key, value in metadata.items():
                        query = query.replace(
                            "created_at: datetime()",
                            f"created_at: datetime(), {key}: ${key}"
                        )
                        params[key] = value
                
                result = session.run(query, params)
                record = result.single()
                
                logger.info(f"Memory node created: {memory_id}")
                return record["m"] if record else None
                
        except Exception as e:
            logger.error(f"Failed to create memory node: {str(e)}")
            raise
    
    async def create_conversation_node(self, conversation_id: int, user_id: int, title: str):
        """Create a conversation node and link it to the user"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})
                CREATE (c:Conversation {
                    conversation_id: $conversation_id,
                    title: $title,
                    created_at: datetime()
                })
                CREATE (u)-[:HAS_CONVERSATION]->(c)
                RETURN c
                """
                
                params = {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "title": title
                }
                
                result = session.run(query, params)
                record = result.single()
                
                logger.info(f"Conversation node created: {conversation_id}")
                return record["c"] if record else None
                
        except Exception as e:
            logger.error(f"Failed to create conversation node: {str(e)}")
            raise
    
    async def extract_and_link_concepts(self, memory_id: str, content: str, concepts: List[str]):
        """Extract concepts from memory content and create relationships"""
        try:
            with self.driver.session() as session:
                # Create or update concepts and link them to the memory
                for concept in concepts:
                    query = """
                    MATCH (m:Memory {memory_id: $memory_id})
                    MERGE (c:Concept {name: $concept})
                    ON CREATE SET c.frequency = 1, c.created_at = datetime()
                    ON MATCH SET c.frequency = c.frequency + 1, c.updated_at = datetime()
                    MERGE (m)-[:MENTIONS]->(c)
                    """
                    
                    session.run(query, {"memory_id": memory_id, "concept": concept.lower()})
                
                logger.info(f"Linked {len(concepts)} concepts to memory {memory_id}")
                
        except Exception as e:
            logger.error(f"Failed to extract and link concepts: {str(e)}")
            raise
    
    async def create_memory_relationship(self, memory_id1: str, memory_id2: str, relationship_type: str, strength: float):
        """Create a relationship between two memories"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m1:Memory {memory_id: $memory_id1})
                MATCH (m2:Memory {memory_id: $memory_id2})
                MERGE (m1)-[r:RELATES_TO]->(m2)
                SET r.type = $relationship_type,
                    r.strength = $strength,
                    r.created_at = datetime()
                RETURN r
                """
                
                params = {
                    "memory_id1": memory_id1,
                    "memory_id2": memory_id2,
                    "relationship_type": relationship_type,
                    "strength": strength
                }
                
                result = session.run(query, params)
                record = result.single()
                
                logger.info(f"Relationship created between memories: {memory_id1} -> {memory_id2}")
                return record["r"] if record else None
                
        except Exception as e:
            logger.error(f"Failed to create memory relationship: {str(e)}")
            raise
    
    async def find_related_memories(self, memory_id: str, max_depth: int = 2, limit: int = 10) -> List[Dict]:
        """Find memories related to a given memory through the graph"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH path = (start:Memory {memory_id: $memory_id})-[:RELATES_TO*1..$max_depth]-(related:Memory)
                RETURN DISTINCT related.memory_id as memory_id,
                       related.content as content,
                       related.importance as importance,
                       related.memory_type as memory_type,
                       length(path) as distance
                ORDER BY related.importance DESC, distance ASC
                LIMIT $limit
                """
                
                params = {
                    "memory_id": memory_id,
                    "max_depth": max_depth,
                    "limit": limit
                }
                
                result = session.run(query, params)
                
                related_memories = []
                for record in result:
                    related_memories.append({
                        "memory_id": record["memory_id"],
                        "content": record["content"],
                        "importance": record["importance"],
                        "memory_type": record["memory_type"],
                        "distance": record["distance"]
                    })
                
                logger.info(f"Found {len(related_memories)} related memories")
                return related_memories
                
        except Exception as e:
            logger.error(f"Failed to find related memories: {str(e)}")
            return []
    
    async def get_user_knowledge_graph(self, user_id: int) -> Dict[str, Any]:
        """Get a summary of the user's knowledge graph"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})
                OPTIONAL MATCH (u)-[:HAS_MEMORY]->(m:Memory)
                OPTIONAL MATCH (m)-[:MENTIONS]->(c:Concept)
                OPTIONAL MATCH (u)-[:HAS_CONVERSATION]->(conv:Conversation)
                RETURN 
                    count(DISTINCT m) as memory_count,
                    count(DISTINCT c) as concept_count,
                    count(DISTINCT conv) as conversation_count,
                    collect(DISTINCT {name: c.name, frequency: c.frequency})[0..10] as top_concepts
                """
                
                result = session.run(query, {"user_id": user_id})
                record = result.single()
                
                if record:
                    return {
                        "memory_count": record["memory_count"],
                        "concept_count": record["concept_count"],
                        "conversation_count": record["conversation_count"],
                        "top_concepts": record["top_concepts"]
                    }
                else:
                    return {
                        "memory_count": 0,
                        "concept_count": 0,
                        "conversation_count": 0,
                        "top_concepts": []
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get knowledge graph summary: {str(e)}")
            return {}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Check the health of the graph service"""
        try:
            with self.driver.session() as session:
                # Test basic connectivity and get node counts
                query = """
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                """
                
                result = session.run(query)
                node_counts = {}
                total_nodes = 0
                
                for record in result:
                    labels = record["labels"]
                    count = record["count"]
                    total_nodes += count
                    
                    for label in labels:
                        node_counts[label] = node_counts.get(label, 0) + count
                
                return {
                    "status": "healthy",
                    "total_nodes": total_nodes,
                    "node_counts": node_counts,
                    "driver_connected": True
                }
                
        except Exception as e:
            logger.error(f"Graph service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "driver_connected": False
            }
    
    async def close(self):
        """Close the Neo4j driver"""
        try:
            if self.driver:
                self.driver.close()
            logger.info("Graph service closed")
        except Exception as e:
            logger.error(f"Error closing graph service: {str(e)}")


# Global graph service instance
graph_service = GraphService()


async def get_graph_service() -> GraphService:
    """Get the global graph service instance"""
    if not graph_service.driver:
        await graph_service.initialize()
    return graph_service 