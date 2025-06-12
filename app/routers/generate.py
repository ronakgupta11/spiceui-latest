from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.graph.workflow import WorkflowGraph

router = APIRouter()
workflow = WorkflowGraph()

class GenerateRequest(BaseModel):
    figma_url: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded image

@router.post("/generate")
async def generate_code(request: GenerateRequest):
    """
    Generate React code from a Figma design or image using the LangGraph workflow
    """
    if not request.figma_url and not request.image:
        raise HTTPException(status_code=400, detail="Either figma_url or image must be provided")
    
    input_data = {}
    if request.figma_url:
        input_data["figma_url"] = request.figma_url
    if request.image:
        input_data["image"] = request.image
    
    try:
        result = await workflow.process(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 