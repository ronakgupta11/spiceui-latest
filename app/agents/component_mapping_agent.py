from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from .base_agent import BaseAgent, AgentState
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.utils.chroma_vector_store import ComponentVectorStore
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComponentMetadata(BaseModel):
    name: str
    description: str
    props: List[Dict[str, Any]]
    examples: List[Dict[str, str]]
    category: str
    tags: List[str]

class LayoutProps(BaseModel):
    order: Optional[int] = None
    flexGrow: Optional[int] = None
    flexBasis: Optional[str] = None
    margin: Optional[Union[int, str]] = None
    padding: Optional[Union[int, str]] = None


class LibraryComponent(BaseModel):
    id: str
    type: str  # Must match library_component.name
    import_: str = Field(..., alias="import")  # From library_component.import
    props: Dict[str, Any]
    layoutProps: LayoutProps = Field(default_factory=LayoutProps)
    children: List[str] = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True  # allows using 'import_' as 'import'
class ComponentMapping(BaseModel):
    components: List[LibraryComponent]
    layout: Optional[Dict[str, Any]] = None
    theme: Optional[Dict[str, str]] = None

class ComponentMappingAgent(BaseAgent[ComponentMapping]):
    def __init__(self):
        super().__init__("component_mapping_agent", model_name="gpt-4o")
        self.set_output_parser(PydanticOutputParser(pydantic_object=ComponentMapping))
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = ComponentVectorStore()

    def validate_input(self, state: AgentState) -> bool:
        return "components" in state.output_data

    async def _flatten_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        flat = []
        def collect(comp_list):
            for c in comp_list:
                flat.append(c)
                if c.get("children"):
                    collect(c["children"])
        collect(components)
        return flat

    async def _find_matching_components(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = {}
        for comp in components:
            query = comp.get("suggested_component_type") or comp.get("type")
            if not query:
                continue
            query += " with properties: " + json.dumps(comp.get("properties", {}))
            matches = self.vector_store.search_components(query, n_results=1)
            if matches:
                match = matches[0]
                full_meta = match['full_metadata']
                results[comp["id"]] = {
                    "name": full_meta.get("component_name"),
                    "metadata": full_meta.get("metadata", {})
                }
        # print("********* results  **********", results)
        return results

    async def _map_components_batch(self, components: List[Dict[str, Any]], metadata_map: Dict[str, Any]) -> List[LibraryComponent]:
        components_data = []
        for comp in components:
            if comp["id"] in metadata_map:
                components_data.append({
                    "id": comp["id"],
                    "component": comp,
                    "library_component": metadata_map[comp["id"]]["metadata"]
                })

        prompt = f"""
You are a code generation engine that transforms visual UI components into React-usable component objects.

You are given:
- `component`: A UI element extracted from an image, including its inferred props, style, and structure.
- `library_component`: A structured schema defining a React component from a UI library. This includes:
  - `name`: Component name (used as the React type).
  - `props`: Supported props with types, default values, and descriptions.
  - `examples`: Real usage examples of this component.
  - `import`: The import statement required for this component.

Your task is to generate a JSON object in the format below that can be used directly for rendering or React code generation.

Output JSON format:
{{
  "components": [
    {{
      "id": "btn-1",                         // Unique identifier
      "type": "Button",                      // Must match library_component.name
      "import": "import {{ Button }} from '@/ui/button'",  // from library_component.import
      "props": {{ "variant": "primary", "label": "Submit" }}, // from component data + validated against library_component.props
      "layoutProps": {{
        "order": 1,
        "flexGrow": 0,
        "flexBasis": "auto",
        "margin": 16,
        "padding": 8
      }},
      "children": ["txt-2"]                  // IDs of child components only
    }}
  ]
}}

Rules:
- Match `type` exactly with `library_component.name`.
- Extract only props that are supported in `library_component.props`.
- Use prop names and types from `library_component`; infer values from the UI component where possible.
- Use `library_component.examples` to infer prop combinations when visual inference is ambiguous.
- `layoutProps` should only include layout-friendly values (no absolute positioning like `x`, `y`, etc).
- Exclude any fields related to geometry or rendering that are not useful in a declarative React context (like `x`, `y`, `width`, `height`, etc).
- Ensure `import` field is taken directly from `library_component.import`.

Only output strict JSON. Do not include any comments or explanations.

Input:
{json.dumps(components_data, indent=2)}
"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.model.ainvoke(messages)

        logger.info("Raw LLM Response:\n%s", response.content)

        parser = PydanticOutputParser(pydantic_object=ComponentMapping)
        try:
            result = parser.parse(response.content)
            return result.components
        except Exception as e:
            logger.error("Parsing failed: %s", e)
            raise

    async def _generate_theme_and_layout(self, layout_info: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        prompt = f"""
Given this layout metadata, extract high-level layout and theme tokens for a React UI:

{json.dumps(layout_info, indent=2)}

Respond ONLY in the structure:

{{
  "layout": {{ "type": "...", "direction": "...", "gap": ... }},
  "theme": {{ "primary": "...", "background": "..." }}
}}

No markdown, no text.
        """
        response = await self._call_llm(prompt, structured_output=False)
        response_dict = json.loads(response)
        return response_dict.get("theme", {}), response_dict.get("layout", {})

    async def process(self, state: AgentState) -> AgentState:
        if not self.validate_input(state):
            state.error = "Missing identified_components"
            return state

        all_components = await self._flatten_components(state.output_data["components"])
        metadata_map = await self._find_matching_components(all_components)
        mapped_components = await self._map_components_batch(all_components, metadata_map)
        theme, layout = await self._generate_theme_and_layout(state.output_data.get("layout_info", {}))

        mapping = ComponentMapping(
            components=mapped_components,
            layout=layout,
            theme=theme
        )

        state.metadata["component_mapping"] = mapping.dict()
        state.output_data = {
            "input_type": state.output_data.get("input_type", "image"),
            "mapped_components": [c.dict() for c in mapped_components],
            "layout": layout,
            "theme": theme
        }

        return state
