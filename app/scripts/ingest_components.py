import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import uuid

# Add the parent directory to sys.path to import from app
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.utils.chroma_vector_store import ComponentVectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('ComponentIngestion')

def ingest_components(docs_dir: str = "component-docs") -> Dict[str, Any]:
    """
    Ingest all component JSON files from the specified directory into ChromaDB.
    This will clear the existing collection and create a new one.
    
    Args:
        docs_dir (str): Path to the directory containing component JSON files
        
    Returns:
        Dict containing ingestion statistics and any errors
    """
    try:
        # Initialize vector store
        vector_store = ComponentVectorStore()
        
        # Convert to Path object for better path handling
        docs_path = Path(docs_dir)
        if not docs_path.exists():
            raise ValueError(f"Directory {docs_dir} does not exist")

        # Clear existing collection
        logger.info("Clearing existing collection...")
        vector_store.clear_collection()
        logger.info("Collection cleared successfully")

        # Get all JSON files
        json_files = list(docs_path.glob("*.json"))
        if not json_files:
            raise ValueError(f"No JSON files found in {docs_dir}")

        logger.info(f"Found {len(json_files)} JSON files to process")

        # Process each JSON file
        successful_ingests = 0
        failed_ingests = 0
        errors = []

        for json_file in json_files:
            try:
                # Read and parse JSON file
                with open(json_file, 'r') as f:
                    component_data = json.load(f)

                # Generate unique ID
                component_id = str(uuid.uuid4())

                # Validate required fields
                if not component_data.get('component_name'):
                    logger.warning(f"Missing component_name in {json_file.name}")
                    continue

                # Add to vector store
                vector_store.add_component(component_id, component_data)
                successful_ingests += 1
                logger.info(f"Successfully ingested {json_file.name}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {json_file.name}: {str(e)}")
                failed_ingests += 1
                errors.append(f"Invalid JSON in {json_file.name}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing {json_file.name}: {str(e)}")
                failed_ingests += 1
                errors.append(f"Error processing {json_file.name}: {str(e)}")

        result = {
            "success": True,
            "message": f"Completed component ingestion. Successfully ingested {successful_ingests} components, failed {failed_ingests} components.",
            "successful_ingests": successful_ingests,
            "failed_ingests": failed_ingests,
            "errors": errors if errors else None
        }
        
        logger.info(result["message"])
        return result

    except Exception as e:
        error_msg = f"Failed to perform bulk ingestion: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "successful_ingests": 0,
            "failed_ingests": len(json_files) if 'json_files' in locals() else 0,
            "errors": [error_msg]
        }

if __name__ == "__main__":
    # You can specify a different directory as a command line argument
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "component-docs"
    
    try:
        result = ingest_components(docs_dir)
        if not result["success"]:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1) 