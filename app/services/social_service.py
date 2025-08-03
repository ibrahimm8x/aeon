"""
Social service for Phase 3 user relationships, shared knowledge, and social intelligence
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.core.logging import get_logger
from app.database.models import (
    User, UserRelationship, SharedKnowledge, AEONInteraction, UserPresence
)
from app.models.aeon import (
    UserRelationship as UserRelationshipModel,
    UserRelationshipCreate,
    SharedKnowledge as SharedKnowledgeModel,
    SharedKnowledgeCreate,
    SharedKnowledgeResponse,
    AEONInteraction as AEONInteractionModel,
    AEONInteractionCreate,
    AEONInteractionResponse,
    SocialNetwork
)

logger = get_logger(__name__)


class SocialService:
    """Service for managing social features and user relationships"""
    
    @staticmethod
    def create_user_relationship(
        db: Session, 
        user_id: int, 
        relationship_data: UserRelationshipCreate
    ) -> UserRelationshipModel:
        """Create a new user relationship"""
        try:
            # Check if relationship already exists
            existing_relationship = db.query(UserRelationship).filter(
                and_(
                    UserRelationship.user_id == user_id,
                    UserRelationship.related_user_id == relationship_data.related_user_id
                )
            ).first()
            
            if existing_relationship:
                # Update existing relationship
                existing_relationship.relationship_type = relationship_data.relationship_type
                existing_relationship.strength = relationship_data.strength
                existing_relationship.shared_interests = relationship_data.shared_interests
                existing_relationship.meta_data = relationship_data.meta_data
                existing_relationship.last_interaction = datetime.utcnow()
                existing_relationship.interaction_count += 1
                
                db.commit()
                db.refresh(existing_relationship)
                
                return UserRelationshipModel.model_validate(existing_relationship)
            
            # Create new relationship
            relationship = UserRelationship(
                user_id=user_id,
                related_user_id=relationship_data.related_user_id,
                relationship_type=relationship_data.relationship_type,
                strength=relationship_data.strength,
                shared_interests=relationship_data.shared_interests,
                meta_data=relationship_data.meta_data
            )
            
            db.add(relationship)
            db.commit()
            db.refresh(relationship)
            
            logger.info(f"Created relationship between user {user_id} and {relationship_data.related_user_id}")
            return UserRelationshipModel.model_validate(relationship)
            
        except Exception as e:
            logger.error(f"Error creating user relationship: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_user_relationships(
        db: Session, 
        user_id: int, 
        relationship_type: Optional[str] = None
    ) -> List[UserRelationshipModel]:
        """Get user relationships"""
        try:
            query = db.query(UserRelationship).filter(UserRelationship.user_id == user_id)
            
            if relationship_type:
                query = query.filter(UserRelationship.relationship_type == relationship_type)
            
            relationships = query.all()
            return [UserRelationshipModel.model_validate(rel) for rel in relationships]
            
        except Exception as e:
            logger.error(f"Error getting user relationships: {e}")
            return []
    
    @staticmethod
    def update_relationship_strength(
        db: Session, 
        user_id: int, 
        related_user_id: int, 
        strength: float
    ) -> bool:
        """Update relationship strength based on interaction"""
        try:
            relationship = db.query(UserRelationship).filter(
                and_(
                    UserRelationship.user_id == user_id,
                    UserRelationship.related_user_id == related_user_id
                )
            ).first()
            
            if relationship:
                relationship.strength = max(0.0, min(1.0, strength))
                relationship.last_interaction = datetime.utcnow()
                relationship.interaction_count += 1
                
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating relationship strength: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def create_shared_knowledge(
        db: Session, 
        user_id: int, 
        knowledge_data: SharedKnowledgeCreate
    ) -> SharedKnowledgeResponse:
        """Create shared knowledge"""
        try:
            knowledge = SharedKnowledge(
                creator_id=user_id,
                content=knowledge_data.content,
                knowledge_type=knowledge_data.knowledge_type,
                tags=knowledge_data.tags or [],
                visibility=knowledge_data.visibility,
                meta_data=knowledge_data.meta_data
            )
            
            db.add(knowledge)
            db.commit()
            db.refresh(knowledge)
            
            # Get creator name
            creator = db.query(User).filter(User.id == user_id).first()
            creator_name = creator.username if creator else None
            
            response = SharedKnowledgeResponse.model_validate(knowledge)
            response.creator_name = creator_name
            
            logger.info(f"Created shared knowledge by user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating shared knowledge: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_shared_knowledge(
        db: Session, 
        user_id: int, 
        knowledge_type: Optional[str] = None,
        visibility: str = "public",
        limit: int = 50
    ) -> List[SharedKnowledgeResponse]:
        """Get shared knowledge based on visibility and filters"""
        try:
            query = db.query(SharedKnowledge)
            
            # Filter by visibility
            if visibility == "public":
                query = query.filter(SharedKnowledge.visibility == "public")
            elif visibility == "friends":
                # Get user's friends
                friend_ids = db.query(UserRelationship.related_user_id).filter(
                    and_(
                        UserRelationship.user_id == user_id,
                        UserRelationship.relationship_type == "friend"
                    )
                ).all()
                friend_ids = [fid[0] for fid in friend_ids]
                friend_ids.append(user_id)  # Include own knowledge
                
                query = query.filter(
                    or_(
                        SharedKnowledge.visibility == "public",
                        SharedKnowledge.creator_id.in_(friend_ids)
                    )
                )
            else:  # private - only own knowledge
                query = query.filter(SharedKnowledge.creator_id == user_id)
            
            # Filter by knowledge type
            if knowledge_type:
                query = query.filter(SharedKnowledge.knowledge_type == knowledge_type)
            
            # Order by creation date
            query = query.order_by(desc(SharedKnowledge.created_at))
            
            # Limit results
            knowledge_list = query.limit(limit).all()
            
            # Add creator names
            result = []
            for knowledge in knowledge_list:
                creator = db.query(User).filter(User.id == knowledge.creator_id).first()
                response = SharedKnowledgeResponse.model_validate(knowledge)
                response.creator_name = creator.username if creator else None
                result.append(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting shared knowledge: {e}")
            return []
    
    @staticmethod
    def upvote_knowledge(db: Session, knowledge_id: int, user_id: int) -> bool:
        """Upvote shared knowledge"""
        try:
            knowledge = db.query(SharedKnowledge).filter(SharedKnowledge.id == knowledge_id).first()
            
            if knowledge:
                knowledge.upvotes += 1
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error upvoting knowledge: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def downvote_knowledge(db: Session, knowledge_id: int, user_id: int) -> bool:
        """Downvote shared knowledge"""
        try:
            knowledge = db.query(SharedKnowledge).filter(SharedKnowledge.id == knowledge_id).first()
            
            if knowledge:
                knowledge.downvotes += 1
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error downvoting knowledge: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def create_aeon_interaction(
        db: Session, 
        aeon_user_id: int, 
        interaction_data: AEONInteractionCreate
    ) -> AEONInteractionResponse:
        """Create AEON-to-AEON interaction"""
        try:
            interaction = AEONInteraction(
                aeon_user_id=aeon_user_id,
                target_aeon_user_id=interaction_data.target_aeon_user_id,
                interaction_type=interaction_data.interaction_type,
                content=interaction_data.content,
                context=interaction_data.context,
                is_public=interaction_data.is_public,
                meta_data=interaction_data.meta_data
            )
            
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            
            # Get AEON names
            aeon_user = db.query(User).filter(User.id == aeon_user_id).first()
            target_aeon = db.query(User).filter(User.id == interaction_data.target_aeon_user_id).first()
            
            response = AEONInteractionResponse.model_validate(interaction)
            response.aeon_name = aeon_user.username if aeon_user else None
            response.target_aeon_name = target_aeon.username if target_aeon else None
            
            logger.info(f"Created AEON interaction from {aeon_user_id} to {interaction_data.target_aeon_user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating AEON interaction: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_aeon_interactions(
        db: Session, 
        aeon_user_id: int, 
        interaction_type: Optional[str] = None,
        is_public: bool = True,
        limit: int = 50
    ) -> List[AEONInteractionResponse]:
        """Get AEON interactions"""
        try:
            query = db.query(AEONInteraction).filter(
                or_(
                    AEONInteraction.aeon_user_id == aeon_user_id,
                    AEONInteraction.target_aeon_user_id == aeon_user_id
                )
            )
            
            if interaction_type:
                query = query.filter(AEONInteraction.interaction_type == interaction_type)
            
            if is_public:
                query = query.filter(AEONInteraction.is_public == True)
            
            query = query.order_by(desc(AEONInteraction.created_at))
            interactions = query.limit(limit).all()
            
            # Add AEON names
            result = []
            for interaction in interactions:
                aeon_user = db.query(User).filter(User.id == interaction.aeon_user_id).first()
                target_aeon = db.query(User).filter(User.id == interaction.target_aeon_user_id).first()
                
                response = AEONInteractionResponse.model_validate(interaction)
                response.aeon_name = aeon_user.username if aeon_user else None
                response.target_aeon_name = target_aeon.username if target_aeon else None
                result.append(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting AEON interactions: {e}")
            return []
    
    @staticmethod
    def respond_to_aeon_interaction(
        db: Session, 
        interaction_id: int, 
        response_content: str
    ) -> bool:
        """Respond to an AEON interaction"""
        try:
            interaction = db.query(AEONInteraction).filter(AEONInteraction.id == interaction_id).first()
            
            if interaction and not interaction.response_content:
                interaction.response_content = response_content
                interaction.response_at = datetime.utcnow()
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error responding to AEON interaction: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_social_network(db: Session, user_id: int) -> SocialNetwork:
        """Get user's social network information"""
        try:
            # Get relationships
            relationships = db.query(UserRelationship).filter(
                UserRelationship.user_id == user_id
            ).all()
            
            # Get shared knowledge
            shared_knowledge = db.query(SharedKnowledge).filter(
                SharedKnowledge.creator_id == user_id
            ).all()
            
            # Get AEON interactions
            aeon_interactions = db.query(AEONInteraction).filter(
                or_(
                    AEONInteraction.aeon_user_id == user_id,
                    AEONInteraction.target_aeon_user_id == user_id
                )
            ).all()
            
            # Calculate network strength (average relationship strength)
            network_strength = 0.0
            if relationships:
                network_strength = sum(rel.strength for rel in relationships) / len(relationships)
            
            # Calculate influence score (based on shared knowledge upvotes and interactions)
            influence_score = 0.0
            total_upvotes = sum(knowledge.upvotes for knowledge in shared_knowledge)
            total_interactions = len(aeon_interactions)
            influence_score = (total_upvotes * 0.7) + (total_interactions * 0.3)
            
            return SocialNetwork(
                user_id=user_id,
                connections=[UserRelationshipModel.model_validate(rel) for rel in relationships],
                shared_knowledge=[SharedKnowledgeModel.model_validate(knowledge) for knowledge in shared_knowledge],
                aeon_interactions=[AEONInteractionModel.model_validate(interaction) for interaction in aeon_interactions],
                network_strength=network_strength,
                influence_score=influence_score,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting social network: {e}")
            return SocialNetwork(user_id=user_id)
    
    @staticmethod
    def find_similar_users(
        db: Session, 
        user_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find users with similar interests based on shared knowledge and relationships"""
        try:
            # Get user's shared knowledge tags
            user_knowledge = db.query(SharedKnowledge).filter(
                SharedKnowledge.creator_id == user_id
            ).all()
            
            user_tags = set()
            for knowledge in user_knowledge:
                if knowledge.tags:
                    user_tags.update(knowledge.tags)
            
            if not user_tags:
                return []
            
            # Find users with similar tags
            similar_users = []
            
            # Query for users who have created knowledge with similar tags
            similar_knowledge = db.query(
                SharedKnowledge.creator_id,
                func.count(SharedKnowledge.id).label('common_knowledge')
            ).filter(
                and_(
                    SharedKnowledge.creator_id != user_id,
                    SharedKnowledge.tags.overlap(list(user_tags))
                )
            ).group_by(SharedKnowledge.creator_id).order_by(
                desc('common_knowledge')
            ).limit(limit).all()
            
            for creator_id, common_count in similar_knowledge:
                user = db.query(User).filter(User.id == creator_id).first()
                if user:
                    # Calculate similarity score
                    user_knowledge_count = db.query(SharedKnowledge).filter(
                        SharedKnowledge.creator_id == creator_id
                    ).count()
                    
                    similarity_score = common_count / max(len(user_tags), user_knowledge_count)
                    
                    similar_users.append({
                        "user_id": user.id,
                        "username": user.username,
                        "similarity_score": similarity_score,
                        "common_knowledge_count": common_count,
                        "total_knowledge_count": user_knowledge_count
                    })
            
            return similar_users
            
        except Exception as e:
            logger.error(f"Error finding similar users: {e}")
            return []
    
    @staticmethod
    def get_active_users(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most active users based on recent activity"""
        try:
            # Get users with recent presence
            recent_presence = db.query(UserPresence).filter(
                UserPresence.last_seen >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(desc(UserPresence.last_seen)).limit(limit).all()
            
            active_users = []
            for presence in recent_presence:
                user = db.query(User).filter(User.id == presence.user_id).first()
                if user:
                    # Get activity metrics
                    knowledge_count = db.query(SharedKnowledge).filter(
                        SharedKnowledge.creator_id == user.id
                    ).count()
                    
                    interaction_count = db.query(AEONInteraction).filter(
                        or_(
                            AEONInteraction.aeon_user_id == user.id,
                            AEONInteraction.target_aeon_user_id == user.id
                        )
                    ).count()
                    
                    active_users.append({
                        "user_id": user.id,
                        "username": user.username,
                        "status": presence.status,
                        "last_seen": presence.last_seen,
                        "knowledge_count": knowledge_count,
                        "interaction_count": interaction_count,
                        "is_aeon": presence.is_aeon
                    })
            
            return active_users
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return [] 