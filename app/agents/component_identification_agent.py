from __future__ import annotations
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from .base_agent import BaseAgent, AgentState
import base64
from langchain_core.output_parsers import PydanticOutputParser

# Recursive UIComponent
class UIComponent(BaseModel):
    id: str = Field(..., description="Unique ID for this component")
    type: str = Field(..., description="UI library component name, e.g. Button, Input")
    props: Dict[str, Any] = Field(
        default_factory=dict,
        description="Props to pass directly into the React component"
    )
    layoutProps: Dict[str, Any] = Field(
        default_factory=dict,
        description="Layout hints: order, flexGrow, flexBasis, margin, padding"
    )
    children: List[UIComponent] = Field(
        default_factory=list,
        description="List of nested component objects"
    )

class ComponentAnalysis(BaseModel):
    components: List[UIComponent] = Field(..., description="Flat array of all components")
    # layout: Dict[str, Any] = Field(
    #     ...,
    #     description="Overall layout hints: type, direction, gap"
    # )
    theme: Dict[str, str] = Field(..., description="Extracted color tokens")

class ComponentIdentificationAgent(BaseAgent[ComponentAnalysis]):
    def __init__(self):
        super().__init__("component_identification_agent", model_name="gpt-4o")
        parser = PydanticOutputParser(pydantic_object=ComponentAnalysis)
        self.set_output_parser(parser)

    def validate_input(self, state: AgentState) -> bool:
        if not state.output_data or state.output_data.get("type") != "image":
            state.error = "Invalid input: expected an image payload"
            return False
        return True

    async def _analyze_components(self, image_data: str) -> ComponentAnalysis:
        system_prompt = """

You are the Component Identification Agent in a multi-step UI-to-code system.

Your job is to generate a **clean, deeply nested, production-grade component tree** that reflects the visual structure of a UI screen. Each component and layout container must be captured as part of a unified tree that can be used to generate code using a custom UI library.

---

## ✅ COMPONENT RULES

1. **All layout primitives are components**:
   - Use: `FlexLayout`, `StackLayout`, `GridLayout` — these are layout containers.
   - They **have `props`** such as `direction`, `align`, `justify`, `gap`, `wrap`, `spacing`, `padding`, `margin`, etc.
   - They contain `children`: a list of components or nested layout containers.

2. **All UI elements are components**:
   - Use components like:
     - `Text` — with a `variant` such as `"h1"`, `"body"`, `"subtitle"`, `"caption"`, `"stat"`, etc.
     - `Icon`, `ArrowUpIcon`, `ArrowDownIcon`
     - `Badge`, `Avatar`, `Progress`
     - `Card` — also used for grouping content and applying background/padding/border
   - Each must define its own `props`, and can appear inside layout containers.

3. **Every node must include**:
   - `id`: a unique string identifier
   - `type`: the name of the component (e.g., `"FlexLayout"`, `"Text"`, `"Card"`)
   - `props`: an object of component-specific props (text, variant, color, size, align, etc.)
   - `children`: optional array of nested child components (only for layout or container-type components)

4. **Layout props are only passed to layout components** like `FlexLayout`, `StackLayout`, `GridLayout`, `Card`.

---

## 🔁 RECURSION AND STRUCTURE

- Layout components like `FlexLayout`, `StackLayout`, etc. contain children which can be either:
  - UI elements (`Text`, `Badge`, `Avatar`, etc.)
  - Other nested layout components

- The tree must preserve visual grouping, nesting, and relative ordering based on the input UI.

---

## ⚠️ STRICT RULES

- Do NOT use `Box`, `Heading`, or generic containers.
- Do NOT use `layoutProps` object — everything goes in the `props` object.
- Do NOT flatten the layout or merge unrelated siblings.
- Do NOT respond with anything other than the strict JSON tree described below.

---

## ✅ OUTPUT FORMAT (STRICT JSON ONLY)

```json
{
  "components": [
    {
      "id": "string",
      "type": "FlexLayout | StackLayout | GridLayout | Card | Text | Icon | Badge | Avatar | Progress......etc",
      "props": {
        // component-specific props
        "direction": "row | column",         // for layout components
        "align": "center | start | end",     // for layout components
        "justify": "space-between | center", // for layout components
        "gap": "number",                     // spacing between children
        "wrap": "boolean",                   // for FlexLayout
        "padding": "number",
        "margin": "number",
        "text": "string",                    // for Text
        "variant": "h1 | h2 | body | stat | caption | subtitle", // for Text
        "color": "string",
        "size": "string",
        "icon": "string",                    // for Icon
        "percent": "number"                  // for Progress, etc.
      },
      "children": [ ... ]  // optional
    }
  ],
  "theme": {
    "primary": "#hex",
    "background": "#hex",
    "text": "#hex",
    "accent": "#hex"
  }
}

"""


        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "Analyze the following UI image and extract the component layout as per the schema."},
                {"type": "image_url", "image_url": {"url": f"{image_data}"}}
            ]}
        ]

        response = await self.model.ainvoke(messages, temperature=0)
        raw = response.content.strip()
        
    


        # parse and sanity-check
        analysis = self.output_parser.parse(raw)
        # ensure no unknown keys
        extra = set(analysis.dict().keys()) - {"components","layout","theme"}
        if extra:
            raise ValueError(f"Unexpected top-level keys: {extra}")
        return analysis

    async def process(self, state: AgentState) -> AgentState:
        if not self.validate_input(state):
            return state

        image_data = state.output_data["raw_input"]["image"]
        try:
            analysis = await self._analyze_components(image_data)
        except Exception as e:
            state.error = f"Component analysis failed: {e}"
            return state

        # store and forward
        state.metadata["component_analysis"] = analysis.dict()
        state.output_data = analysis.dict()
        return state
