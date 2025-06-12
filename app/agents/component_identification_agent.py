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
        system_prompt = '''

You are the **Component Identification Agent** in a multi-stage system designed to generate high-fidelity UI component trees from images.

Your mission is to interpret a user interface image and produce a deeply **semantic, production-grade component tree** in strict JSON format. This tree will later be used to generate React code using components from the Salt Design System.

---

## 🧠 BEHAVIOR GUIDELINES

You must **think deeply and intentionally** before generating the component tree. Do **not just mimic layout and text**. Instead, **interpret** the image to determine the **actual component types** best suited for each UI element. Use the most semantically correct component from the list below.

Ask yourself:
- What does this element *actually do*?
- Is this just a `Text`, or is it part of a `Badge`, `Stepper`, `Toast`, or `Card`?
- Is this icon for feedback, navigation, or status?
- Is this layout purely visual, or does it serve as a grouping container like a`Panel`?
- For each component, do its children require a layout wrapper? If so, which layout component should be used to maintain the structure and hierarchy?
- Is there a need for additional components, such as `FormFieldLabel`, to enhance the functionality of the component, like `FormField`?

You are expected to **observe icons, input styles, layouts, and interactions** to deduce the correct component. Each component must come from the available design system below — **do not make up or use generic components.**

---

## ✅ ALLOWED COMPONENTS

You can only use components from these packages:

**@salt-ds/core**
- Accordion, AccordionGroup, AccordionHeader, AccordionPanel, AriaAnnouncerProvider, Avatar, Badge, Banner, BannerActions, BannerContent, BorderItem, BorderLayout, BreakpointProvider, Button, Card, Checkbox, CheckboxGroup, CircularProgress, Code, ComboBox, CompactInput, CompactPaginator, ConditionalScrimWrapper, Dialog, DialogActions, DialogCloseButton, DialogContent, DialogHeader, Display1, Display2, Display3, Display4, Divider, Drawer, DrawerCloseButton, Dropdown, FileDropZone, FileDropZoneTrigger, FlexItem, FlexLayout, FloatingComponentProvider, FloatingPlatformProvider, FlowLayout, FormField, FormFieldHelperText, FormFieldLabel, GoToInput, GridItem, GridLayout, H1, H2, H3, H4, Input, InteractableCard, InteractableCardGroup, Label, LinearProgress, Link, LinkAction, LinkCard, ListBox, Menu, MenuBase, MenuGroup, MenuItem, MenuPanel, MenuPanelBase, MenuTrigger, MultilineInput, NavigationItem, NavigationItemAction, Option, OptionGroup, OptionList, OptionListBase, Overlay, OverlayHeader, OverlayPanel, OverlayPanelCloseButton, OverlayPanelContent, OverlayTrigger, PageButton, PageRanges, Pagination, Paginator, Panel, ParentChildLayout, Pill, PillInput, RadioButton, RadioButtonGroup, RangeSlider, SaltProvider, SaltProviderNext, Scrim, SegmentedButtonGroup, SemanticIconProvider, SkipLink, Slider, SliderThumb, SliderTooltip, SliderTrack, Spinner, SpinnerSVG, SpinnerSizeValues, SplitLayout, StackLayout, StatusAdornment, StatusIndicator, Step, StepExpandTrigger, StepScreenReaderOnly, StepText, Stepper, StepperProvider, Switch, Tag, Text, TextAction, TextNotation, Toast, ToastContent, ToastGroup, ToggleButton, ToggleButtonGroup, Tooltip, TooltipBase

**@salt-ds/icons**
- Use correct icons like `ArrowUpIcon`, `ArrowDownIcon`, or specific semantic icons.

**@salt-ds/countries**
- `CountrySymbol`

**@salt-ds/lab**
- `Calendar`, `Carousel`, `DateInput`, `DatePicker`, `LocalizationProvider`, `NumberInput`, `StaticList`, `SystemStatus`, `Tabs`, `TokenizedInput`

**@salt-ds/ag-grid-theme**
- AG Grid components where tabular data is shown.

**@salt-ds/react-resizable-panels-theme**
- `Splitter`

---

## 🔁 STRUCTURE AND LOGIC

1. Use layout primitives like `FlexLayout`, `StackLayout`, and `GridLayout` to arrange children.
- **Do not use `Box` or div-like generics**.
- Layouts have layout-specific props only (`direction`, `gap`, `align`, etc.).
2. All textual elements must use the `Text` component with an appropriate `variant` (`h1`, `body`, `caption`, `subtitle`, `stat`).
3. Always use `Icon` with correct semantic name if a graphical symbol is shown.
4. Use `FormField`, `Input`, `Select`, `DatePicker`, `NumberInput`, etc., wherever appropriate — **never use plain text or layout to mock inputs**. Ensure that components like `FormField` are used with their corresponding `FormFieldLabel` for proper labeling.
5. **Be especially cautious** about layout structuring. Ensure that the hierarchy and grouping of components strictly reflect the visual UI. Deep nesting should be preserved to accurately represent the intended layout.
6. Use `Avatar` only for profile/user images.
7. Ensure deep nesting reflects hierarchy and grouping in the visual UI.
8. For each component, evaluate if its children require a layout wrapper. If they do, choose the appropriate layout component to ensure proper rendering and structure.

---

## ⚠️ STRICT RULES

- NO `Box`, NO `div`, NO arbitrary containers.
- NO text-based mimicry of UI elements (e.g., don’t use `Text` to fake buttons).
- DO NOT flatten layout — preserve nested grouping.
- Only include properties relevant to the component.
- All layout-related props must go inside `props` of the layout component.
- Do NOT use `layoutProps` as a separate object.
- You MUST always return sizing values in pixels (px) for spacing, size (for icons and other elements), and gap and other layout properties.

---

## 📥 INPUT

You will receive:
1. A screenshot of a user interface (`image_url`)
2. The instruction: “Analyze the following UI image and extract the component layout as per the schema.”

---

## ✅ OUTPUT FORMAT

Respond **only** with strict JSON of the following structure:

```json
{
"components": [
{
"id": "unique_string_id",
"type": "ComponentNameFromListAbove",
"props": {
// Only props relevant to this component
"direction": "row | column",
"align": "center | start | end",
"justify": "space-between | center",
"gap": "number",
"wrap": true,
"padding": "number",
"margin": "number",
"text": "string",
"styleAs": "\"code\" | \"h1\" | \"h2\" | \"h3\" | \"h4\" | \"label\" | \"display1\" | \"display2\" | \"display3\" | \"display4\" | \"notation\" | \"action\"",
"color": "\"error\" | \"warning\" | \"success\" | \"info\" | \"primary\" | \"secondary\" | \"inherit\" | \"white\" | \"black\" | \"red\" "",
"size": "string",
"icon": "ArrowUpIcon| InfoIcon | OtherSaltIcon",
"percent": "number"
},
"children": [ ... ]
}
],
"theme": {
"primary": "#hex",
"background": "#hex",
"text": "#hex",
"accent": "#hex"
}
}
```
'''
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
