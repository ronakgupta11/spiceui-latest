from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.agents.chat_based_code_modification_agent import ChatBasedCodeModificationAgent, ChatMessage

router = APIRouter()
modification_agent = ChatBasedCodeModificationAgent()

class CodeModificationRequest(BaseModel):
    current_code: Dict[str, str]
    chat_history: List[ChatMessage]
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
        response = await modification_agent.modify_code(request)
        
        return CodeModificationResponse(
            modified_files=response.files,
            changes=response.changes,
            warnings=response.warnings,
            explanation=response.explanation
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 