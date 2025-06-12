import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import os
from datetime import datetime

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

logger = logging.getLogger('ComponentListing')

def list_components(output_file: str = "component_list.txt") -> Dict[str, Any]:
    """
    List all available components and save them to a file.
    
    Args:
        output_file (str): Path to the output file where component names will be saved
        
    Returns:
        Dict containing listing statistics
    """
    try:
        # Initialize vector store
        vector_store = ComponentVectorStore()
        
        # Get all components
        logger.info("Fetching all components...")
        results = vector_store.collection.get()
        
        if not results or not results['ids']:
            logger.warning("No components found in the collection")
            return {
                "success": True,
                "message": "No components found in the collection",
                "total_components": 0,
                "output_file": output_file
            }

        # Extract component names and categories
        components = []
        for i, metadata in enumerate(results['metadatas']):
            component_name = metadata.get('component_name', 'Unknown')
            category = metadata.get('category', 'Uncategorized')
            components.append({
                'name': component_name,
                'category': category
            })

        # Sort components by category and name
        components.sort(key=lambda x: (x['category'], x['name']))

        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_file, 'w') as f:
            f.write(f"Component List - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            current_category = None
            for component in components:
                # Write category header if category changes
                if component['category'] != current_category:
                    current_category = component['category']
                    f.write(f"\n{current_category}\n")
                    f.write("-" * len(current_category) + "\n")
                
                f.write(f"- {component['name']}\n")

        # Also create a JSON file with more detailed information
        json_output = output_path.with_suffix('.json')
        with open(json_output, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_components': len(components),
                'components': components
            }, f, indent=2)

        result = {
            "success": True,
            "message": f"Successfully listed {len(components)} components",
            "total_components": len(components),
            "output_file": output_file,
            "json_output_file": str(json_output)
        }
        
        logger.info(result["message"])
        return result

    except Exception as e:
        error_msg = f"Failed to list components: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "total_components": 0,
            "output_file": output_file
        }

if __name__ == "__main__":
    # You can specify a different output file as a command line argument
    output_file = sys.argv[1] if len(sys.argv) > 1 else "component_list.txt"
    
    try:
        result = list_components(output_file)
        if not result["success"]:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1) 