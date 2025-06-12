from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent, AgentState
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

class OutputMetadata(BaseModel):
    """Structured output for generation metadata"""
    generation_time: str = Field(description="Time of code generation")
    input_type: str = Field(description="Type of input (image/figma)")
    component_count: int = Field(description="Number of components generated")
    dependencies: List[str] = Field(description="Required dependencies")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during generation")

class OutputResponse(BaseModel):
    """Structure for the final output response"""
    code: Dict[str, str] = Field(description="Generated or modified code files")
    metadata: Dict[str, Any] = Field(description="Metadata about the generation/modification process")
    chat_history: List[Dict[str, str]] = Field(default_factory=list, description="Updated chat history")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during the process")
    explanation: Optional[str] = Field(None, description="Explanation of the changes made")

class OutputAgent(BaseAgent[OutputResponse]):
    def __init__(self):
        super().__init__("output_agent", model_name="gpt-4-turbo-preview")
        
        # Set up output parser
        parser = PydanticOutputParser(pydantic_object=OutputResponse)
        self.set_output_parser(parser)
    
    def validate_input(self, state: AgentState) -> bool:
        """Validate that the input state contains required information"""
        if not state.input_data:
            state.error = "No input data provided"
            return False

        # For chat-based modifications
        if state.input_data.get("is_chat_modification", False):
            required_fields = ["modified_files", "changes", "warnings", "explanation"]
        # For initial code generation
        else:
            required_fields = ["generated_files"]

        for field in required_fields:
            if field not in state.output_data:
                state.error = f"Missing required field in output data: {field}"
                return False

        return True
    
    async def _format_output(self, state: AgentState) -> OutputResponse:
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
        
        return OutputResponse(
            code=state.output_data["react_code"],
            metadata={
                "type": "initial_generation",
                "timestamp": datetime.utcnow().isoformat(),
                "components": state.output_data.get("mapped_components", []),
                "dependencies": state.output_data.get("dependencies", []),
                "hooks": code_generation.get("hooks", [])
            },
            warnings=warnings
        )
    
    async def process(self, state: AgentState) -> AgentState:
        """Process the input state and format the final output"""
        if not self.validate_input(state):
            return state

        try:
            # Get the current timestamp
            timestamp = datetime.utcnow().isoformat()

            # Prepare the response based on the type of request
            if state.input_data.get("is_chat_modification", False):
                # Handle chat-based modification output
                response = OutputResponse(
                    code=state.output_data["modified_files"],
                    metadata={
                        "type": "chat_modification",
                        "timestamp": timestamp,
                        "changes": state.output_data["changes"],
                        "previous_modifications": state.metadata.get("modifications", [])
                    },
                    chat_history=state.input_data.get("chat_history", []),
                    warnings=state.output_data.get("warnings", []),
                    explanation=state.output_data.get("explanation")
                )
            else:
                # Handle initial code generation output
                response = OutputResponse(
                    code=state.output_data["generated_files"],
                    metadata={
                        "type": "initial_generation",
                        "timestamp": timestamp,
                        "components": state.output_data.get("components", []),
                        "dependencies": state.metadata.get("code_generation", {}).get("dependencies", []),
                        "hooks": state.metadata.get("code_generation", {}).get("hooks", [])
                    },
                    warnings=state.output_data.get("warnings", [])
                )

            # Update state with formatted output
            state.output_data = response.dict()

        except Exception as e:
            state.error = f"Failed to format output: {str(e)}"
            return state

        return state 