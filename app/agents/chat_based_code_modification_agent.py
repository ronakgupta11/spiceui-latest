from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent
from app.utils.chroma_vector_store import ComponentVectorStore
from langchain.output_parsers import PydanticOutputParser
import json
import logging
import sys

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

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: str = Field(..., description="Timestamp of the message")

class CodeModificationRequest(BaseModel):
    current_code: Dict[str, str]
    chat_history: List[ChatMessage]
    available_components: List[Dict[str, Any]]
    previous_modifications: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class ModifiedCodeResponse(BaseModel):
    files: Dict[str, str]
    changes: List[Dict[str, Any]]
    warnings: List[str] = Field(default_factory=list)
    explanation: str
    remaining_chat_history: List[ChatMessage] = Field(default_factory=list)

class ChatBasedCodeModificationAgent(BaseAgent[ModifiedCodeResponse]):
    def __init__(self):
        super().__init__("chat_based_code_modification_agent", model_name="gpt-4o")
        self.set_output_parser(PydanticOutputParser(pydantic_object=ModifiedCodeResponse))
        self.vector_store = ComponentVectorStore()
        logger.info("ChatBasedCodeModificationAgent initialized")

    def build_prompt(self, request: CodeModificationRequest) -> str:
        latest_message = request.chat_history[-1]
        logger.info("Building prompt with latest message")
        logger.debug("Latest message: %s", latest_message.dict())
        
        prompt = f"""
You are a code modification agent helping to improve React code based on user feedback.

## Current Code
{json.dumps(request.current_code, indent=2)}

## Latest User Request
{latest_message.content}

## Available UI Components
{json.dumps(request.available_components, indent=2)}

### Instructions:
- ONLY use components from the available list.
- Apply best practices in React and TypeScript.
- Keep changes minimal, targeted, and consistent with prior updates.
- Comment on non-obvious logic where needed.
- Respond in the following JSON structure:

{{
  "files": {{
    "filename.tsx": "updated source"
  }},
  "changes": [
    {{
      "file": "filename.tsx",
      "type": "modification/addition/removal",
      "description": "what was changed"
    }}
  ],
  "warnings": ["any warnings if applicable"],
  "explanation": "short explanation of the reasoning and goals of the changes",
  "remaining_chat_history": []
}}
""".strip()
        
        logger.debug("Generated prompt: %s", prompt)
        return prompt

    async def modify_code(self, request: CodeModificationRequest) -> ModifiedCodeResponse:
        """
        Modify code based on the user's request and chat history.
        This is the main entry point for the API.
        """
        logger.info("Starting code modification")
        logger.debug("Request details: %s", request.dict())
        
        if not request.chat_history:
            logger.warning("No chat messages provided")
            return ModifiedCodeResponse(
                files=request.current_code,
                changes=[],
                warnings=["No chat messages provided"],
                explanation="No user instruction available to act on.",
                remaining_chat_history=[]
            )

        try:
            prompt = self.build_prompt(request)
            logger.info("Calling LLM with prompt")
            response = await self._call_llm(prompt)
            logger.debug("Received LLM response: %s", response.dict())
            
            response.remaining_chat_history = request.chat_history[1:]
            return response
        except Exception as e:
            logger.error("Error during code modification: %s", str(e), exc_info=True)
            # Return a structured error response instead of raising
            return ModifiedCodeResponse(
                files=request.current_code,
                changes=[],
                warnings=[f"Error during code modification: {str(e)}"],
                explanation="Failed to process the modification request.",
                remaining_chat_history=request.chat_history
            )
