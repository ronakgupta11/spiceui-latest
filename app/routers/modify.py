from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.agents.chat_based_code_modification_agent import ChatBasedCodeModificationAgent, ChatMessage, CodeModificationRequest as AgentCodeModificationRequest
import logging
import sys
from datetime import datetime

# Set up logging with more detailed configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure the logger is set to DEBUG level
logger.setLevel(logging.DEBUG)

router = APIRouter()
modification_agent = ChatBasedCodeModificationAgent()

class ChatMessageRequest(BaseModel):
    role: str
    content: str
    timestamp: str

class CodeModificationRequest(BaseModel):
    current_code: Dict[str, str]
    chat_history: List[ChatMessageRequest]
    available_components: List[Dict[str, Any]]

class CodeModificationResponse(BaseModel):
    modified_files: Dict[str, str]
    changes: List[Dict[str, Any]]
    warnings: List[str]
    explanation: str

@router.post("/modify", response_model=CodeModificationResponse)
async def modify_code(request: CodeModificationRequest):
    """
    Modify React code based on user feedback and chat history using the ChatBasedCodeModificationAgent
    """
    try:
        logger.info("Backend modify_code - Received request")
        logger.debug("Request details: %s", request.dict())
        
        # Convert request to agent's expected format
        agent_request = AgentCodeModificationRequest(
            current_code=request.current_code,
            chat_history=[
                ChatMessage(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp
                ) for msg in request.chat_history
            ],
            available_components=request.available_components
        )
        
        logger.info("Calling modification agent")
        response = await modification_agent.modify_code(agent_request)
        logger.debug("Agent response: %s", response.dict())
        
        return CodeModificationResponse(
            modified_files=response.files,
            changes=response.changes,
            warnings=response.warnings,
            explanation=response.explanation
        )

    except Exception as e:
        logger.error("Backend modify_code - Error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 