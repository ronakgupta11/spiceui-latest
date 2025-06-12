from typing import Dict, Any, List
from pydantic import BaseModel, Field
from .base_agent import BaseAgent, AgentState
from langchain_core.output_parsers import PydanticOutputParser

class ModifiedCode(BaseModel):
    """Structured output for modified code"""
    files: Dict[str, str] = Field(description="Mapping from file path to modified file contents")
    changes: List[Dict[str, Any]] = Field(description="List of changes made to the code")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during modification")

class CodeModificationAgent(BaseAgent[ModifiedCode]):
    def __init__(self):
        super().__init__("code_modification_agent", model_name="gpt-4o")
        self.set_output_parser(PydanticOutputParser(pydantic_object=ModifiedCode))

    def validate_input(self, state: AgentState) -> bool:
        if not state.output_data or "generated_files" not in state.output_data:
            state.error = "Invalid input state: missing generated files"
            return False
        if not state.input_data.get("modification_prompt"):
            state.error = "No modification prompt provided"
            return False
        return True

    async def _modify_code(self, files: Dict[str, str], prompt: str) -> ModifiedCode:
        """Modify the code based on the user's prompt"""
        system_prompt = """
You are a code modification expert. Your task is to modify the provided React code based on the user's prompt.
Follow these rules:
1. Only make changes that are explicitly requested
2. Maintain the existing code structure and patterns
3. Preserve all functionality not mentioned in the modification request
4. Keep the same file organization
5. Document any changes made

Return a JSON object with:
1. The modified files (only include files that were changed)
2. A list of changes made
3. Any warnings or potential issues
"""

        user_prompt = f"""
Modification request: {prompt}

Current code files:
{files}

Please modify the code according to the request and return the changes in the specified format.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.model.ainvoke(messages)
        return self.output_parser.parse(response.content)

    async def process(self, state: AgentState) -> AgentState:
        if not self.validate_input(state):
            return state

        files = state.output_data["generated_files"]
        prompt = state.input_data["modification_prompt"]

        try:
            modified_code = await self._modify_code(files, prompt)
            
            # Update the state with modified files
            state.output_data["generated_files"].update(modified_code.files)
            state.metadata["modification"] = {
                "changes": modified_code.changes,
                "warnings": modified_code.warnings
            }
            
            # Add any warnings to the output
            if modified_code.warnings:
                if "warnings" not in state.output_data:
                    state.output_data["warnings"] = []
                state.output_data["warnings"].extend(modified_code.warnings)

        except Exception as e:
            state.error = f"Code modification failed: {str(e)}"
            return state

        return state 