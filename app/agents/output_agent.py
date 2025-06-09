from typing import Dict, Any, List
from pydantic import BaseModel, Field
from .base_agent import BaseAgent, AgentState
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

class OutputMetadata(BaseModel):
    """Structured output for generation metadata"""
    generation_time: str = Field(description="Time of code generation")
    input_type: str = Field(description="Type of input (image/figma)")
    component_count: int = Field(description="Number of components generated")
    dependencies: List[str] = Field(description="Required dependencies")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during generation")

class OutputAgent(BaseAgent[OutputMetadata]):
    def __init__(self):
        super().__init__("output_agent", model_name="gpt-4-turbo-preview")
        
        # Set up output parser
        parser = PydanticOutputParser(pydantic_object=OutputMetadata)
        self.set_output_parser(parser)
    
    def validate_input(self, state: AgentState) -> bool:
        if not state.output_data or "react_code" not in state.output_data:
            state.error = "Invalid input state: missing generated React code"
            return False
        return True
    
    async def _format_output(self, state: AgentState) -> OutputMetadata:
        """Format the final output with metadata"""
        # Collect metadata from previous agents
        validation_metadata = state.metadata.get("validation", {})
        component_analysis = state.metadata.get("component_analysis", {})
        component_mapping = state.metadata.get("component_mapping", {})
        code_generation = state.metadata.get("code_generation", {})
        
        # Generate warnings if any
        warnings = []
        if validation_metadata.get("confidence", 1.0) < 0.8:
            warnings.append("Low confidence in UI validation")
        if not component_analysis.get("accessibility_features"):
            warnings.append("No accessibility features identified")
        
        return OutputMetadata(
            generation_time=datetime.utcnow().isoformat(),
            input_type=state.output_data["input_type"],
            component_count=len(state.output_data.get("mapped_components", [])),
            dependencies=state.output_data.get("dependencies", []),
            warnings=warnings
        )
    
    async def process(self, state: AgentState) -> AgentState:
        if not self.validate_input(state):
            return state
            
        # Format output with metadata
        output_metadata = await self._format_output(state)
        
        # Prepare final output
        final_output = {
            "status": "success",
            "code": state.output_data["react_code"],
            "metadata": output_metadata.dict(),
            "warnings": output_metadata.warnings
        }
        
        state.output_data = final_output
        return state 