from fastapi import APIRouter, HTTPException
from app.models.component_schema import ComponentIngestRequest, ComponentIngestResponse, ComponentMetadata
from app.utils.scraper import ComponentScraper
from app.utils.chroma_vector_store import ComponentVectorStore
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()
scraper = ComponentScraper()
vector_store = ComponentVectorStore()      

@router.post("/ingest-component", response_model=ComponentIngestResponse)
async def ingest_component(request: ComponentIngestRequest):
    """
    Ingest a component either from metadata or by scraping a documentation URL.
    """
    try:
        # Generate a unique ID for the component
        component_id = str(uuid.uuid4())
        logger.debug(f"Generated component ID: {component_id}")
        
        # Get component metadata
        if request.metadata:
            logger.debug("Ingesting component with metadata")
            metadata = request.metadata.dict()
            logger.debug(f"Metadata: {metadata}")
        elif request.documentation_url:
            logger.debug(f"Ingesting component with documentation URL: {request.documentation_url}")
            metadata = await scraper.scrape_component(str(request.documentation_url))
            logger.debug(f"Scraped metadata: {metadata}")
        else:
            raise HTTPException(
                status_code=400,
                detail="Either metadata or documentation_url must be provided"
            )
        
        # Validate required fields
        if not metadata.get('component_name'):
            raise HTTPException(
                status_code=400,
                detail="Component name is required"
            )
        
        print("metadata", metadata)
        # Add component to vector store
        try:
            vector_store.add_component(component_id, metadata)
            logger.debug(f"Successfully added component to vector store: {component_id}")
        except Exception as e:
            logger.error(f"Failed to add component to vector store: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store component: {str(e)}"
            )
        
        # Create response metadata
        response_metadata = ComponentMetadata(
            component_name=metadata['component_name'],
            description=metadata['metadata']['description'],
            props=metadata['metadata']['props'],
            examples=metadata['metadata']['examples'],
            category=metadata['metadata']['category'],
            tags=metadata['metadata']['tags'],
            when_to_use=metadata['metadata'].get('when_to_use'),
            when_not_to_use=metadata['metadata'].get('when_not_to_use'),
            import_statement=metadata['metadata'].get('import_statement')
        )
        
        return ComponentIngestResponse(
            success=True,
            component_id=component_id,
            message=f"Successfully ingested component: {metadata['component_name']}",
            component_metadata=response_metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during component ingestion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest component: {str(e)}"
        )

@router.get("/components/{component_id}", response_model=ComponentIngestResponse)
async def get_component(component_id: str):
    """
    Retrieve a component by its ID.
    """
    try:
        logger.debug(f"Attempting to retrieve component with ID: {component_id}")
        component = vector_store.get_component(component_id)
        
        if not component:
            logger.warning(f"Component not found with ID: {component_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Component with ID {component_id} not found"
            )
        
        logger.debug(f"Successfully retrieved component: {component}")
        return ComponentIngestResponse(
            success=True,
            component_id=component_id,
            message=f"Successfully retrieved component: {component['metadata']['name']}",
            component_metadata=component['metadata']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving component: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve component: {str(e)}"
        ) 