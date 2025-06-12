from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent
from app.utils.chroma_vector_store import ComponentVectorStore
from langchain.output_parsers import PydanticOutputParser
import json

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
        super().__init__("chat_based_code_modification_agent", model_name="gpt-4-turbo-preview")
        self.set_output_parser(PydanticOutputParser(pydantic_object=ModifiedCodeResponse))
        self.vector_store = ComponentVectorStore()

    def build_prompt(self, request: CodeModificationRequest) -> str:
        latest_message = request.chat_history[0]
        return f"""
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

    async def modify_code(self, request: CodeModificationRequest) -> ModifiedCodeResponse:
        """
        Modify code based on the user's request and chat history.
        This is the main entry point for the API.
        """
        if not request.chat_history:
            return ModifiedCodeResponse(
                files=request.current_code,
                changes=[],
                warnings=["No chat messages provided"],
                explanation="No user instruction available to act on.",
                remaining_chat_history=[]
            )

        try:
            prompt = self.build_prompt(request)
            response = await self._call_llm(prompt)
            response.remaining_chat_history = request.chat_history[1:]
            return response
        except Exception as e:
            # Return a structured error response instead of raising
            return ModifiedCodeResponse(
                files=request.current_code,
                changes=[],
                warnings=[f"Error during code modification: {str(e)}"],
                explanation="Failed to process the modification request.",
                remaining_chat_history=request.chat_history
            )
