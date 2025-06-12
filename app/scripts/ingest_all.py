import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import uuid
import os

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

def ingest_all(components_dir: str = "component-docs", icons_file: str = "icon-docs/icon-docs.json") -> Dict[str, Any]:
    """
    Ingest all components and icons into ChromaDB.
    This will clear the existing collection and create a new one.
    
    Args:
        components_dir (str): Path to the directory containing component JSON files
        icons_file (str): Path to the icon documentation JSON file
        
    Returns:
        Dict containing ingestion statistics and any errors
    """
    try:
        # Initialize vector store
        vector_store = ComponentVectorStore()
        
        # Clear existing collection
        logger.info("Clearing existing collection...")
        vector_store.clear_collection()
        logger.info("Collection cleared successfully")

        # Initialize counters
        successful_component_ingests = 0
        failed_component_ingests = 0
        successful_icon_ingests = 0
        failed_icon_ingests = 0
        errors = []

        # Process components
        components_path = Path(components_dir)
        if not components_path.exists():
            raise ValueError(f"Directory {components_dir} does not exist")

        json_files = list(components_path.glob("*.json"))
        if not json_files:
            logger.warning(f"No JSON files found in {components_dir}")
        else:
            logger.info(f"Found {len(json_files)} component JSON files to process")

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
                    successful_component_ingests += 1
                    logger.info(f"Successfully ingested component {json_file.name}")

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in {json_file.name}: {str(e)}")
                    failed_component_ingests += 1
                    errors.append(f"Invalid JSON in {json_file.name}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing {json_file.name}: {str(e)}")
                    failed_component_ingests += 1
                    errors.append(f"Error processing {json_file.name}: {str(e)}")

        # Process icons
        icons_path = Path(icons_file)
        if not icons_path.exists():
            logger.warning(f"Icons file {icons_file} does not exist")
        else:
            try:
                with open(icons_path, 'r') as f:
                    icons = json.load(f)

                logger.info(f"Found {len(icons)} icons to process")

                for icon in icons:
                    try:
                        # Add to vector store
                        vector_store.add_icon(icon)
                        successful_icon_ingests += 1
                        logger.info(f"Successfully ingested icon {icon.get('component_name', 'unknown')}")

                    except Exception as e:
                        logger.error(f"Error processing icon {icon.get('component_name', 'unknown')}: {str(e)}")
                        failed_icon_ingests += 1
                        errors.append(f"Error processing icon {icon.get('component_name', 'unknown')}: {str(e)}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in icons file: {str(e)}")
                failed_icon_ingests = len(icons) if 'icons' in locals() else 0
                errors.append(f"Invalid JSON in icons file: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing icons file: {str(e)}")
                failed_icon_ingests = len(icons) if 'icons' in locals() else 0
                errors.append(f"Error processing icons file: {str(e)}")

        result = {
            "success": True,
            "message": (
                f"Completed ingestion. "
                f"Successfully ingested {successful_component_ingests} components and {successful_icon_ingests} icons. "
                f"Failed {failed_component_ingests} components and {failed_icon_ingests} icons."
            ),
            "successful_component_ingests": successful_component_ingests,
            "failed_component_ingests": failed_component_ingests,
            "successful_icon_ingests": successful_icon_ingests,
            "failed_icon_ingests": failed_icon_ingests,
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
            "successful_component_ingests": 0,
            "failed_component_ingests": len(json_files) if 'json_files' in locals() else 0,
            "successful_icon_ingests": 0,
            "failed_icon_ingests": len(icons) if 'icons' in locals() else 0,
            "errors": [error_msg]
        }

if __name__ == "__main__":
    # You can specify different directories as command line arguments
    components_dir = sys.argv[1] if len(sys.argv) > 1 else "component-docs"
    icons_file = sys.argv[2] if len(sys.argv) > 2 else "icon-docs/icon-docs.json"
    
    try:
        result = ingest_all(components_dir, icons_file)
        if not result["success"]:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1) 