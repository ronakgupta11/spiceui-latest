from typing import Any, Dict, Optional, TypeVar, Generic
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

T = TypeVar('T', bound=BaseModel)

class AgentState(BaseModel):
    """Base state class for all agents"""
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseAgent(Generic[T]):
    """Base agent class that all other agents will inherit from"""
    
    def __init__(self, name: str, model_name: str = "gpt-4o"):
        self.name = name
        self.model = ChatOpenAI(
            model_name=model_name,
            temperature=0.1,
            streaming=True
        )
        self.output_parser = None
    
    def set_output_parser(self, parser: PydanticOutputParser[T]):
        """Set the output parser for structured output"""
        self.output_parser = parser
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Process the input state and return the updated state
        To be implemented by child classes
        """
        raise NotImplementedError("Child classes must implement process method")
    
    def validate_input(self, state: AgentState) -> bool:
        """
        Validate the input state
        To be implemented by child classes
        """
        raise NotImplementedError("Child classes must implement validate_input method")
    
    async def _call_llm(self, prompt: str, structured_output: bool = True) -> Any:
        """Call the LLM with the given prompt and parse the output if structured"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.model.ainvoke(messages)
        
        if structured_output and self.output_parser:
            return self.output_parser.parse(response.content)
        return response.content 