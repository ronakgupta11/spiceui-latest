from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl

class ComponentProp(BaseModel):
    name: str
    type: str
    description: str
    required: bool = False
    default: Optional[Any] = None

class ComponentExample(BaseModel):
    jsx: str
    description: Optional[str] = None

class ComponentMetadata(BaseModel):
    component_name: str
    description: str
    props: List[ComponentProp]
    examples: List[Dict[str, str]]
    category: str
    tags: List[str]
    when_to_use: Optional[List[str]] = None
    when_not_to_use: Optional[List[str]] = None
    import_statement: Optional[str] = None

class ComponentIngestRequest(BaseModel):
    component_name: str
    metadata: Optional[ComponentMetadata] = None
    documentation_url: Optional[HttpUrl] = None

class ComponentIngestResponse(BaseModel):
    success: bool
    component_id: str
    message: str
    component_metadata: ComponentMetadata

class AnnotationRegion(BaseModel):
    x: float
    y: float
    width: float
    height: float
    confidence: float
    component_match: Optional[ComponentMetadata] = None

class AnnotationRequest(BaseModel):
    image_url: Optional[HttpUrl] = None
    figma_url: Optional[HttpUrl] = None
    image_file: Optional[bytes] = None

class AnnotationResponse(BaseModel):
    regions: List[AnnotationRegion]
    hierarchy: Dict[str, Any]

class CodeGenerationRequest(BaseModel):
    annotations: AnnotationResponse
    target_library: str

class CodeGenerationResponse(BaseModel):
    code: str
    components_used: List[str]
    warnings: Optional[List[str]] = None 