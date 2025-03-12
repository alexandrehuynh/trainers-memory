from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from typing import Dict, Any, Optional, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

# Import auth and DB dependencies
from ..auth_utils import validate_api_key  # Changed to use validate_api_key consistently
from ..db import get_async_db, AsyncClientRepository
from ..utils.response import StandardResponse

# Create router
router = APIRouter()

@router.post("/personalized-messages", response_model=Dict[str, Any])
async def generate_personalized_message(
    client_id: uuid.UUID = Query(..., description="Client ID to generate message for"),
    message_type: str = Query(..., description="Type of message (reminder, motivation, progress, recommendation)"),
    customization: Optional[str] = Body(None, description="Additional customization or context for the message"),
    client_info: Dict[str, Any] = Depends(validate_api_key),  # Updated to use validate_api_key
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate a personalized message for a client.
    
    Creates a message tailored to the client based on their workout history, goals, and progress.
    Message types include:
    - reminder: Reminds client of upcoming sessions or tasks
    - motivation: Motivational message to keep client engaged
    - progress: Highlights client's progress and achievements
    - recommendation: Provides tailored recommendations based on client's goals and history
    
    The message can be further customized by providing additional context.
    """
    try:
        # Get client data
        client_repo = AsyncClientRepository(db)
        client = await client_repo.get(client_id)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
        
        # Validate message type
        valid_types = ["reminder", "motivation", "progress", "recommendation"]
        if message_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid message_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # This would call a more sophisticated service to generate personalized messages
        # For now, return template-based messages
        message_templates = {
            "reminder": f"Hi {client.name}, just a friendly reminder about your upcoming training session. Looking forward to seeing you!",
            "motivation": f"Great job on your recent workouts, {client.name}! Keep up the amazing work - you're making fantastic progress!",
            "progress": f"Congratulations {client.name}! You've been consistently showing up and putting in the work. Your dedication is truly inspiring!",
            "recommendation": f"Based on your recent workouts, {client.name}, I'd recommend focusing a bit more on recovery and mobility this week. Let me know if you need some specific exercises!"
        }
        
        # Get the base message
        message = message_templates[message_type]
        
        # Customize if additional context provided
        if customization:
            message += f" {customization}"
        
        return StandardResponse.success(
            data={
                "client_id": str(client_id),
                "client_name": client.name,
                "message_type": message_type,
                "message": message,
                "delivery_channels": ["email", "sms", "app"]  # Suggested delivery channels
            },
            message="Personalized message generated successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating personalized message: {str(e)}"
        ) 