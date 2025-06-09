from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .base_agent import BaseAgent, AgentState
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import json

class GeneratedCode(BaseModel):
    files: Dict[str, str] = Field(description="Mapping from file path to file contents")
    dependencies: List[str] = Field(description="Required dependencies")
    hooks: Optional[List[str]] = Field(None, description="Required React hooks")

class CodeGenerationAgent(BaseAgent[GeneratedCode]):
    def __init__(self):
        super().__init__("code_generation_agent", model_name="gpt-4o")
        self.set_output_parser(PydanticOutputParser(pydantic_object=GeneratedCode))
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = Chroma(collection_name="components", embedding_function=self.embeddings)

    def validate_input(self, state: AgentState) -> bool:
        if not state.output_data or "mapped_components" not in state.output_data:
            state.error = "Invalid input state: missing mapped_components"
            return False
        return True

    async def _generate_component_code(self, component: Dict[str, Any]) -> str:
        prompt = f"""
Generate a React component using SaltDS UI library based on this mapping:

{json.dumps(component, indent=2)}

Requirements:
1. Use exact props and styles from the mapping
2. Use SaltDS components
3. Include text_content if present
4. Handle children recursively
5. Use inline styles only when necessary

Return only the component code in JSX format.
"""
        return await self._call_llm(prompt, structured_output=False)

    async def _generate_main_app_code(self, components: List[Dict[str, Any]], theme: Dict[str, Any], layout: Dict[str, Any]) -> str:
        prompt = f"""
Generate a React App component that uses these mapped components:

Components:
{json.dumps(components, indent=2)}

Theme:
{json.dumps(theme, indent=2)}

Layout:
{json.dumps(layout, indent=2)}

Requirements:
1. Use SaltDS components
2. Apply theme and layout settings
3. Render all components in their correct hierarchy
4. Use inline styles only when necessary

Return only the App component code in JSX format.
"""
        return await self._call_llm(prompt, structured_output=False)

    async def process(self, state: AgentState) -> AgentState:
        if not self.validate_input(state):
            return state

        mapped_components = state.output_data["mapped_components"]
        components = mapped_components
        theme = state.output_data.get("theme", {})
        layout = state.output_data.get("layout", {})

        files = {}
        for comp in components:
            code = await self._generate_component_code(comp)
            files[f"src/components/{comp['id']}.jsx"] = code

        main_app_code = await self._generate_main_app_code(components, theme, layout)
        files["src/App.jsx"] = main_app_code

        files["src/index.jsx"] = """
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root')
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

        files["package.json"] = """
{
  "name": "saltds-app",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "saltds": "latest"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
"""

        state.metadata["code_generation"] = {
            "files": files,
            "dependencies": ["saltds", "react", "react-dom"],
            "hooks": ["useState", "useEffect"]
        }

        state.output_data = {
            "input_type": state.output_data.get("input_type", "image"),
            "generated_files": files,
            "dependencies": ["saltds", "react", "react-dom"],
            "hooks": ["useState", "useEffect"]
        }

        return state