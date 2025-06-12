from typing import Dict, Any, List, Set, Optional
from pydantic import BaseModel, Field
from .base_agent import BaseAgent, AgentState
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.utils.chroma_vector_store import ComponentVectorStore
import json
import logging
from dataclasses import dataclass
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComponentProps(BaseModel):
    """Detailed component props information"""
    name: str = Field(description="Prop name")
    type: str = Field(description="Prop type")
    required: bool = Field(description="Whether the prop is required")
    default: Optional[Any] = Field(description="Default value if any")
    description: str = Field(description="Prop description")


class IconInfo(BaseModel):
    """Information about an icon"""
    name: str = Field(description="Icon name")
    import_statement: str = Field(description="Import statement")
    description: str = Field(description="Icon description")
    category: str = Field(description="Icon category")
    tags: List[str] = Field(description="Related tags")
    when_to_use: List[str] = Field(description="Common usage contexts")
    synonyms: List[str] = Field(description="Alternative names/terms")
    props: List[ComponentProps] = Field(description="Available props")

class DetailedComponent(BaseModel):
    """Detailed component information"""
    name: str = Field(description="Component name")
    import_statement: str = Field(description="Import statement")
    description: str = Field(description="Component description")
    category: str = Field(description="Component category")
    props: List[ComponentProps] = Field(description="Available props")
    when_to_use: List[str] = Field(description="Usage information")
    tags: List[str] = Field(description="Tags")

class LayoutInfo(BaseModel):
    """Layout component information"""
    type: str = Field(description="Layout type (e.g., flex, grid)")
    props: List[ComponentProps] = Field(description="Layout props")
    best_practices: List[str] = Field(description="Layout best practices")
    responsive_behavior: Dict[str, Any] = Field(description="Responsive behavior")

class StaticComponentMapping(BaseModel):
    """Complete mapping of all components and layouts"""
    components: List[DetailedComponent] = Field(description="List of detailed components")
    layouts: List[DetailedComponent] = Field(description="List of layout components")
    icons: List[IconInfo] = Field(description="List of icons")
    theme: Dict[str, Any] = Field(description="Theme information")

class StaticComponentMappingAgent(BaseAgent[StaticComponentMapping]):
    def __init__(self):
        super().__init__("static_component_mapping_agent")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = ComponentVectorStore()
        self._component_cache = {}
        self._layout_cache = {}
        self._icon_cache = {}

    def validate_input(self, state: AgentState) -> bool:
        valid = "components" in state.output_data
        if not valid:
            logger.error("Validation failed: 'components' not in state.output_data")
        return valid

    def _extract_unique_components(self, components: List[Dict[str, Any]]) -> Set[str]:
        """Extract unique component types from the component tree"""
        unique_types = set()
        try:
            def extract_types(comp_list):
                for comp in comp_list:
                    unique_types.add(comp["type"])
                    if comp.get("children"):
                        extract_types(comp["children"])
            extract_types(components)
        except Exception as e:
            logger.exception(f"Failed to extract unique components: {e}")
        return unique_types

    def _extract_unique_icons(self, components: List[Dict[str, Any]]) -> Set[str]:
        """Extract unique icon names from the component tree"""
        unique_icons = set()
        try:
            def extract_icons(comp_list):
                for comp in comp_list:
                    if comp["type"] == "Icon" and "icon" in comp.get("props", {}):
                        unique_icons.add(comp["props"]["icon"])
                    if comp.get("children"):
                        extract_icons(comp["children"])
            extract_icons(components)
        except Exception as e:
            logger.exception(f"Failed to extract unique icons: {e}")
        return unique_icons

    def parse_component_props(self, raw_props: Any) -> List[ComponentProps]:
        parsed = []
        try:
            if isinstance(raw_props, dict):
                for name, config in raw_props.items():
                    if isinstance(config, dict):
                        parsed.append(ComponentProps(
                            name=name,
                            type=config.get("type", "any"),
                            required=config.get("required", False),
                            default=config.get("defaultValue", None),  # map to correct field
                            description=config.get("description", "")
                        ))
                    else:
                        # fallback for non-dict configs
                        parsed.append(ComponentProps(
                            name=name,
                            type="any",
                            required=False,
                            default=None,
                            description=str(config) if config is not None else ""
                        ))
            else:
                # fallback if props isn't a dict at all
                parsed.append(ComponentProps(
                    name="unknown",
                    type="any",
                    required=False,
                    default=None,
                    description=""
                ))
        except Exception as e:
            logger.exception(f"Failed to parse component props: {e}")
        return parsed

    def _find_component_details(self, component_type: str) -> Optional[DetailedComponent]:
        """Find detailed component information from vector store"""
        try:
            if component_type in self._component_cache:
                logger.debug(f"Component '{component_type}' found in cache.")
                return self._component_cache[component_type]

            logger.info(f"Searching for component details: {component_type}")
            
            # First try exact match by component name
            results = self.vector_store.collection.get(
                where={"component_name": component_type},
                include=["metadatas", "documents"]
            )
            
            if results and results['ids']:
                logger.info(f"Found exact match for component: {component_type}")
                metadata = results['metadatas'][0]
                full_metadata = json.loads(results['documents'][0])
                
                # Parse JSON strings for list fields
                tags = json.loads(metadata.get('tags', '[]')) if isinstance(metadata.get('tags'), str) else metadata.get('tags', [])
                when_to_use = json.loads(metadata.get('when_to_use', '[]')) if isinstance(metadata.get('when_to_use'), str) else metadata.get('when_to_use', [])
                props = json.loads(metadata.get('props', '{}')) if isinstance(metadata.get('props'), str) else metadata.get('props', {})
                
                component = DetailedComponent(
                    name=metadata.get("component_name", "Unknown"),
                    import_statement=metadata.get("import_statement") or "",
                    description=metadata.get("description") or "",
                    category=metadata.get("category") or "Uncategorized",
                    props=self.parse_component_props(props),
                    when_to_use=when_to_use,
                    tags=tags
                )
                
                self._component_cache[component_type] = component
                return component
            
            # If no exact match, fall back to semantic search
            logger.info(f"No exact match found, trying semantic search for: {component_type}")
            matches = self.vector_store.search_components(component_type, n_results=1)
            if not matches:
                logger.warning(f"No matches found for component: {component_type}")
                return None

            match = matches[0]
            full_metadata = match['full_metadata']
            metadata = full_metadata.get("metadata")

            if not metadata:
                logger.warning(f"No metadata found for component: {component_type}")
                return None

            # Parse JSON strings for list fields
            tags = json.loads(metadata.get('tags', '[]')) if isinstance(metadata.get('tags'), str) else metadata.get('tags', [])
            when_to_use = json.loads(metadata.get('when_to_use', '[]')) if isinstance(metadata.get('when_to_use'), str) else metadata.get('when_to_use', [])
            props = json.loads(metadata.get('props', '{}')) if isinstance(metadata.get('props'), str) else metadata.get('props', {})

            component = DetailedComponent(
                name=metadata.get("component_name", "Unknown"),
                import_statement=metadata.get("import_statement") or "",
                description=metadata.get("description") or "",
                category=metadata.get("category") or "Uncategorized",
                props=self.parse_component_props(props),
                when_to_use=when_to_use,
                tags=tags
            )

            self._component_cache[component_type] = component
            logger.info(f"Component details found and cached: {component_type}")
            return component
        except Exception as e:
            logger.exception(f"Failed to find component details for '{component_type}': {e}")
            return None

    def _find_layout_details(self, layout_type: str) -> Optional[LayoutInfo]:
        """Find layout component information from vector store"""
        try:
            if layout_type in self._layout_cache:
                logger.debug(f"Layout '{layout_type}' found in cache.")
                return self._layout_cache[layout_type]

            logger.info(f"Searching for layout details: {layout_type}")
            matches = self.vector_store.search_components(f"layout {layout_type}", n_results=1)
            if not matches:
                logger.warning(f"No matches found for layout: {layout_type}")
                return None

            match = matches[0]
            
    
            full_metadata = match.get('full_metadata', {})

            # Use metadata from full_metadata if available, otherwise use metadata
            metadata = full_metadata.get('metadata', {})

            layout = DetailedComponent(
                name=metadata.get("component_name", "Unknown"),
                import_statement=metadata.get("import_statement") or "",
                description=metadata.get("description") or "",
                category=metadata.get("category") or "Uncategorized",
                props=self.parse_component_props(metadata.get("props", {})),
                when_to_use=metadata.get("when_to_use", []),
                tags=metadata.get("tags", [])
            )

            self._layout_cache[layout_type] = layout
            logger.info(f"Layout details found and cached: {layout_type}")
            return layout
        except Exception as e:
            logger.exception(f"Failed to find layout details for '{layout_type}': {e}")
            return None

    def _find_icon_details(self, icon_name: str) -> Optional[IconInfo]:
        """Find icon information from vector store"""
        try:
            if icon_name in self._icon_cache:
                logger.debug(f"Icon '{icon_name}' found in cache.")
                return self._icon_cache[icon_name]

            logger.info(f"Searching for icon details: {icon_name}")
            
            # Clean up icon name for search
            search_name = icon_name.replace("Icon", "").strip()
            
            # Try exact search first
            matches = self.vector_store.search_icons(search_name, n_results=1)
            if not matches:
                logger.warning(f"No exact matches found for icon: {icon_name}")
                # Try with synonyms
                matches = self.vector_store.search_icons(f"icon {search_name}", n_results=1)
                if not matches:
                    logger.warning(f"No matches found for icon: {icon_name}")
                    return None

            match = matches[0]
            # Get metadata from the correct location in the search results
            metadata = match.get('metadata', {})
            full_metadata = match.get('full_metadata', {})

            # Use metadata from full_metadata if available, otherwise use metadata
            icon_data = full_metadata.get('metadata', metadata)


            icon = IconInfo(
                name=icon_data.get("component_name", "Unknown"),
                import_statement=icon_data.get("import_statement", ""),
                description=icon_data.get("description", ""),
                category=icon_data.get("category", "Icon"),
                tags=icon_data.get("tags", []),
                when_to_use=icon_data.get("when_to_use", []),
                synonyms=icon_data.get("synonyms", []),
                props=self.parse_component_props(icon_data.get("props", {}))
            )

            self._icon_cache[icon_name] = icon
            logger.info(f"Icon details found and cached: {icon_name}")
            return icon
        except Exception as e:
            logger.exception(f"Failed to find icon details for '{icon_name}': {e}")
            return None

    async def process(self, state: AgentState) -> AgentState:
        try:
            logger.info("Starting StaticComponentMappingAgent.process")
            if not self.validate_input(state):
                state.error = "Missing components in input state"
                logger.error("Process failed: Missing components in input state")
                return state

            # Extract unique components, layouts, and icons
            try:
                unique_components = self._extract_unique_components(state.output_data["components"])
                logger.info(f"Unique components extracted: {unique_components}")
            except Exception as e:
                logger.exception(f"Failed to extract unique components: {e}")
                state.error = f"Failed to extract unique components: {e}"
                return state

            try:
                unique_icons = self._extract_unique_icons(state.output_data["components"])
                logger.info(f"Unique icons extracted: {unique_icons}")
            except Exception as e:
                logger.exception(f"Failed to extract unique icons: {e}")
                state.error = f"Failed to extract unique icons: {e}"
                return state

            # Find details for each component
            components = []
            for comp_type in unique_components:
                if comp_type != "Icon":  # Skip icons as they're handled separately
                    try:
                        details = self._find_component_details(comp_type)
                        if details:
                            components.append(details)
                        else:
                            logger.warning(f"No details found for component: {comp_type}")
                    except Exception as e:
                        logger.exception(f"Error finding details for component '{comp_type}': {e}")

            # Find layout details
            layouts = []
            if "layout" in state.output_data:
                layout_type = state.output_data["layout"].get("type")
                if layout_type:
                    try:
                        layout_details = self._find_layout_details(layout_type)
                        if layout_details:
                            layouts.append(layout_details)
                        else:
                            logger.warning(f"No details found for layout: {layout_type}")
                    except Exception as e:
                        logger.exception(f"Error finding details for layout '{layout_type}': {e}")

            # Find icon details
            icons = []
            for icon_name in unique_icons:
                try:
                    icon_details = self._find_icon_details(icon_name)
                    if icon_details:
                        icons.append(icon_details)
                    else:
                        logger.warning(f"No details found for icon: {icon_name}")
                except Exception as e:
                    logger.exception(f"Error finding details for icon '{icon_name}': {e}")

            # Create the mapping
            try:
                mapping = StaticComponentMapping(
                    components=components,
                    layouts=layouts,
                    icons=icons,
                    theme=state.output_data.get("theme", {})
                )
                logger.info("StaticComponentMapping created successfully.")
            except Exception as e:
                logger.exception(f"Failed to create StaticComponentMapping: {e}")
                state.error = f"Failed to create StaticComponentMapping: {e}"
                return state

            # Update state
            try:
                state.metadata["static_component_mapping"] = mapping.dict()
                state.output_data.update({
                    "detailed_components": [c.dict() for c in components],
                    "detailed_layouts": [l.dict() for l in layouts],
                    "detailed_icons": [i.dict() for i in icons]
                })
                logger.info("State updated with detailed components, layouts, and icons.")
            except Exception as e:
                logger.exception(f"Failed to update state with mapping: {e}")
                state.error = f"Failed to update state with mapping: {e}"
                return state

            logger.info("StaticComponentMappingAgent.process completed successfully.")
            return state
        except Exception as e:
            logger.exception(f"Unhandled exception in StaticComponentMappingAgent.process: {e}")
            state.error = f"Unhandled exception: {e}"
            return state