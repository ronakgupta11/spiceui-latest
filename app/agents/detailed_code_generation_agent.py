from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .base_agent import BaseAgent, AgentState
from langchain_core.output_parsers import PydanticOutputParser
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeneratedCode(BaseModel):
    """Structure for generated code output"""
    files: Dict[str, str] = Field(description="Mapping from file path to file contents")
    dependencies: List[str] = Field(description="Required dependencies")
    hooks: Optional[List[str]] = Field(None, description="Required React hooks")

class DetailedCodeGenerationAgent(BaseAgent[GeneratedCode]):
    def __init__(self):
        super().__init__("detailed_code_generation_agent", model_name="gpt-4o")
        self.set_output_parser(PydanticOutputParser(pydantic_object=GeneratedCode))

    def validate_input(self, state: AgentState) -> bool:
        """Validate that the input state contains required component mapping information"""
        required_fields = [
            "components",  # Component tree
            "detailed_components",  # UI library component details
            "detailed_icons",  # Icon details
            "detailed_layouts"  # Layout details
        ]
        
        if not state.output_data:
            state.error = "Invalid input state: missing output_data"
            return False
            
        for field in required_fields:
            if field not in state.output_data:
                state.error = f"Invalid input state: missing {field}"
                return False
                
        return True

    async def _generate_component_code(self, 
                                    component: Dict[str, Any],
                                    detailed_components: List[Dict[str, Any]],
                                    detailed_icons: List[Dict[str, Any]],
                                    detailed_layouts: List[Dict[str, Any]]) -> str:
        """Generate React component code using detailed component information"""
        
        # Find matching component details
        component_details = next(
            (c for c in detailed_components if c["name"].lower() == component["type"].lower()),
            None
        )
        
        # Find matching icon details if component uses icons
        icon_details = None
        if component.get("props", {}).get("icon"):
            icon_details = next(
                (i for i in detailed_icons if i["name"].lower() == component["props"]["icon"].lower()),
                None
            )

        prompt = f"""
Generate a React component using the SaltDS UI library based on the following information:

Component Tree Node:
{json.dumps(component, indent=2)}

Component Library Details:
{json.dumps(component_details, indent=2) if component_details else "No matching component found in library"}

Icon Details (if applicable):
{json.dumps(icon_details, indent=2) if icon_details else "No icon used"}

Available Layouts:
{json.dumps(detailed_layouts, indent=2)}

Requirements:
1. Use exact props and styles from the component tree
2. Use SaltDS components with proper imports
3. Include text_content if present
4. Handle children recursively
5. Use proper layout components when needed
6. Include proper icon imports and usage
7. Add proper comments for complex logic
8. Use inline styles only when necessary

Return only the component code in JSX format.
"""
        return await self._call_llm(prompt, structured_output=False)

    async def _generate_main_app_code(self, 
                                    components: List[Dict[str, Any]],
                                    detailed_components: List[Dict[str, Any]],
                                    detailed_icons: List[Dict[str, Any]],
                                    detailed_layouts: List[Dict[str, Any]],
                                    theme: Dict[str, Any]) -> str:
        """Generate the main App component code"""
        
        system_prompt = f'''
You are a React code generation engine trained to produce clean, correct, and fully structured Salt Design System JSX code.

Your job is to:
1. Interpret a deeply nested component tree.
2. Map it precisely to SaltDS components, layout primitives, and icons.
3. Analyze and utilize each available UI component's props to determine the most efficient way to render the UI.
4. Apply correct props, layout rules, spacing (in 8px units), and semantic structure.
5. Output only the final `App` component JSX code, including `export default function App` — no markdown, explanations, or commentary.

Rules you must follow:
- Think through the hierarchy, layout, and available component props before writing JSX.
- You MUST apply layout primitives like `FlexLayout`, `StackLayout`, `GridLayout` instead of generic wrappers like `div`.
- Use child JSX (e.g., `<Text>hello</Text>`) rather than props like `text="hello"` unless the API explicitly requires it.
- Leverage component-specific props effectively to enhance functionality and visual appeal.
- Apply spacing via `padding`, `margin`, `gap` using 8px units (`gap=4` = 32px) and floor it to nearest integer.
- You MUST always return sizing values in integers for size (for icons and other elements) using 8px units and floor it to nearest integer (e.g., `size=4` = 32px).
- Group and deduplicate imports by SaltDS package (e.g., `@salt-ds/core`, `@salt-ds/icons`).
- Ensure all components used in the JSX are correctly imported from the given import statements in the `Available Components` or `Available Icons` section do not invent or assume import statements.
- Ensure functional correctness, hierarchy fidelity, and visual layout match.
- Do not guess — use only the components, icons, and layout options explicitly provided.

Generate **only** the valid JSX of a functional `App` component with the appropriate imports.
'''
        user_prompt = f'''
Component Tree:
{json.dumps(components, indent=2)}

Available Components:
{json.dumps(detailed_components, indent=2)}

Available Icons:
{json.dumps(detailed_icons, indent=2)}

Theme:
{json.dumps(theme, indent=2)}

Instructions:
- Use the data above to map each node in the component tree to a real SaltDS component.
- Apply correct layout structure and prop mapping.
- Do not include markdown formatting or explanations.
- Only return the JSX for the App component.

'''

# Instructions:
# 1. Use SaltDS components and icons with **correct and minimal imports**. Club all imports from the same package together (e.g., `import A, B from "@salt-ds/icons"`).
# 2. Apply the theme configuration correctly.
# 3. **Respect correct JSX usage**. For example:
#    - Use `<Text>example</Text>` instead of `<Text text="example" />`
#    - Use `<Button>Click me</Button>` instead of `<Button label="Click me" />` unless the API demands it.
# 4. Use layout components appropriately to reflect the `Component Tree` hierarchy.
# 5. When using spacing, paddings, margins, and gaps, **use numbers according to the 1 unit = 8px rule**. For example:
#    - For 40px spacing, use `gap={5}` (not `gap={40}`).
# 6. Prefer `props` over `style`, and use inline styles **only if absolutely required**.
# 7. Ensure all components are rendered in their correct order and nested correctly inside their respective parent layout components.
# 8. Include **clear inline comments** only where necessary (such as for conditionals or computed logic), but do not overcomment obvious UI structure.

# Only return the final React JSX code of the App component.  
# Do not return any extra text, explanations, descriptions, markdown formatting, or surrounding commentary.
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]
        response = await self.model.ainvoke(messages, temperature=0)
        raw = response.content.strip()
        return raw


    async def process(self, state: AgentState) -> AgentState:
        """Process the input state and generate React code"""
        try:
            if not self.validate_input(state):
                return state

            # Extract required information from state
            components = state.output_data["components"]
            detailed_components = state.output_data["detailed_components"]
            detailed_icons = state.output_data["detailed_icons"]
            detailed_layouts = state.output_data["detailed_layouts"]
            theme = state.output_data.get("theme", {})

            # Generate component files
            files = {}
            # for comp in components:
            #     try:
            #         code = await self._generate_component_code(
            #             comp,
            #             detailed_components,
            #             detailed_icons,
            #             detailed_layouts
            #         )
            #         files[f"src/components/{comp['id']}.jsx"] = code
            #     except Exception as e:
            #         logger.error(f"Error generating code for component {comp['id']}: {e}")
            #         continue

            # Generate main App component
            try:
                main_app_code = await self._generate_main_app_code(
                    components,
                    detailed_components,
                    detailed_icons,
                    detailed_layouts,
                    theme
                )
                files["src/App.tsx"] = main_app_code
            except Exception as e:
                logger.error(f"Error generating main App component: {e}")
                state.error = f"Failed to generate main App component: {e}"
                return state

            # Add index file
            files["src/index.tsx"] = """
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

            # Add package.json
            files["package.json"] = """
{
  "name": "saltds-app",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^4.9.0",
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

            # Update state with generated code
            state.metadata["code_generation"] = {
                "files": files,
                "dependencies": ["saltds", "react", "react-dom", "typescript"],
                "hooks": ["useState", "useEffect"]
            }

            state.output_data.update({
                "generated_files": files,
            })

            return state

        except Exception as e:
            logger.exception(f"Error in DetailedCodeGenerationAgent.process: {e}")
            state.error = f"Failed to generate code: {e}"
            return state 