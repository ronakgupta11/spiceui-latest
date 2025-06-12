import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
import os
import logging
from pathlib import Path
import stat

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ComponentVectorStore:
    def __init__(self, persist_directory: str = "data/chroma"):
        # Convert to absolute path
        self.persist_directory = str(Path(persist_directory).absolute())
        logger.debug(f"Using persist directory: {self.persist_directory}")
        
        # Ensure directory exists with proper permissions
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            # Set directory permissions to 755
            os.chmod(self.persist_directory, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        except Exception as e:
            logger.error(f"Failed to create or set permissions on directory {self.persist_directory}: {str(e)}")
            raise
        
        try:
            # Initialize ChromaDB client with explicit settings
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True
                )
            )
            
            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name="components",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Verify collection
            logger.debug(f"Collection name: {self.collection.name}")
            logger.debug(f"Collection count: {self.collection.count()}")
            
            # Initialize sentence transformer for embeddings
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.debug("ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding for a text using the sentence transformer model."""
        return self.embedding_model.encode(text).tolist()
    
    def add_icon(self, icon_data: Dict[str, Any]) -> None:
        """Add an icon to the vector store.
        
        Args:
            icon_data: Dictionary containing icon information with the following structure:
                {
                    "component_name": str,
                    "import": str,
                    "synonym": List[str],
                    "tags": List[str],
                    "when_to_use": List[str]
                }
        """
        try:
            logger.debug(f"Adding icon: {icon_data['component_name']}")
            
            # Generate a unique ID for the icon
            icon_id = f"icon_{icon_data['component_name'].lower()}"

            # Prepare metadata for ChromaDB
            metadata_for_chroma = {
                'component_name': icon_data['component_name'],
                'import_statement': icon_data['import'],
                'description': f"Icon for {icon_data['component_name'].lower().replace('icon', '')}",
                'category': 'Icon',
                'props': json.dumps({
                    'size': {
                        'type': 'string | number',
                        'required': False,
                        'defaultValue': 'medium',
                        'description': 'Size of the icon'
                    },
                    'color': {
                        'type': 'string',
                        'required': False,
                        'defaultValue': 'inherit',
                        'description': 'Color of the icon'
                    }
                }),
                'tags': json.dumps(icon_data.get('tags', [])),
                'synonyms': json.dumps(icon_data.get('synonym', [])),
                'when_to_use': json.dumps(icon_data.get('when_to_use', []))
            }
            
            # Create a text representation for embedding
            # Include component name, synonyms, and tags for better searchability
            component_text = (
                f"{icon_data['component_name']} "
                f"{' '.join(icon_data.get('synonym', []))} "
                f"{' '.join(icon_data.get('tags', []))} "
                f"{' '.join(icon_data.get('when_to_use', []))}"
            )
            
            # Create embedding
            embedding = self._create_embedding(component_text)
            
            # Prepare full metadata for document
            full_metadata = {
                'component_name': icon_data['component_name'],
                'import_statement': icon_data['import'],
                'description': metadata_for_chroma['description'],
                'category': 'Icon',
                'props': json.loads(metadata_for_chroma['props']),
                'tags': icon_data.get('tags', []),
                'synonyms': icon_data.get('synonym', []),
                'when_to_use': icon_data.get('when_to_use', [])
            }
            
            # Add to collection
            self.collection.add(
                ids=[icon_id],
                embeddings=[embedding],
                metadatas=[metadata_for_chroma],
                documents=[json.dumps(full_metadata)]
            )
            
            # Verify the icon was added
            count_after = self.collection.count()
            logger.debug(f"Collection count after adding: {count_after}")
            
            # Verify the icon exists
            result = self.collection.get(ids=[icon_id])
            if not result['ids']:
                raise Exception("Icon was not added successfully")
            
            logger.debug(f"Successfully added icon {icon_data['component_name']} to ChromaDB")
            
        except Exception as e:
            logger.error(f"Error adding icon to ChromaDB: {str(e)}")
            raise

    def add_component(self, component_id: str, metadata: Dict[str, Any]) -> None:
        """Add a component to the vector store."""
        try:
            logger.debug(f"Adding component with ID: {component_id}")
            logger.debug(f"Metadata: {metadata}")
            
            # Convert lists to JSON strings for ChromaDB
            metadata_for_chroma = {
                'component_name': metadata['component_name'],
                'description': metadata['metadata']['description'],
                'props': json.dumps(metadata['metadata']['props']),
                'examples': json.dumps(metadata['metadata'].get('examples', [])),
                'category': metadata['metadata'].get('category', ""),
                'tags': json.dumps(metadata['metadata'].get('tags', []))
            }
            
            
            # Create a text representation of the component for embedding
            component_text = f"{metadata['component_name']} {metadata['metadata']['description']} {' '.join(metadata['metadata'].get('tags', []))}"
            
            # Create embedding
            embedding = self._create_embedding(component_text)
            
            # Add to collection
            self.collection.add(
                ids=[component_id],
                embeddings=[embedding],
                metadatas=[metadata_for_chroma],
                documents=[json.dumps(metadata)]
            )
            
            # Verify the component was added
            count_after = self.collection.count()
            logger.debug(f"Collection count after adding: {count_after}")
            
            # Verify the component exists
            result = self.collection.get(ids=[component_id])
            if not result['ids']:
                raise Exception("Component was not added successfully")
            
            logger.debug(f"Successfully added component {component_id} to ChromaDB")
            
        except Exception as e:
            logger.error(f"Error adding component to ChromaDB: {str(e)}")
            raise
    
    def get_component(self, component_id: str) -> Dict[str, Any]:
        """Get a component by its ID."""
        try:
            logger.debug(f"Attempting to retrieve component with ID: {component_id}")
            
            # Log the current state of the collection
            logger.debug(f"Collection name: {self.collection.name}")
            logger.debug(f"Collection count: {self.collection.count()}")
            
            # Get the component
            result = self.collection.get(ids=[component_id])
            logger.debug(f"Raw ChromaDB query result: {result}")
            
            if not result['ids']:
                logger.warning(f"No component found with ID: {component_id}")
                return None
            
            # Parse the metadata
            metadata = result['metadatas'][0]
            parsed_metadata = {
                'component_name': metadata['component_name'],
                'description': metadata['description'],
                'props': json.loads(metadata['props']),
                'examples': json.loads(metadata['examples']),
                'category': metadata['category'],
                'tags': json.loads(metadata['tags'])
            }
            
            # Log the parsed result
            parsed_result = {
                'id': result['ids'][0],
                'metadata': parsed_metadata,
                'document': json.loads(result['documents'][0])
            }
            logger.debug(f"Parsed result: {parsed_result}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error retrieving component from ChromaDB: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def search_components(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for components similar to the query, returning parsed metadata and full document."""
        try:
            logger.debug(f"Searching for components with query: {query}")
            # Create embedding for query
            query_embedding = self._create_embedding(query)
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            components = []
            for i in range(len(results['ids'][0])):
                meta = results['metadatas'][0][i]
                # Parse fields that are stored as JSON strings
                meta['tags'] = json.loads(meta['tags']) if isinstance(meta['tags'], str) else meta['tags']
                meta['props'] = json.loads(meta['props']) if isinstance(meta['props'], str) else meta['props']
                meta['examples'] = json.loads(meta['examples']) if isinstance(meta['examples'], str) else meta['examples']
                # Add full document
                full_metadata = json.loads(results['documents'][0][i]) if results['documents'][0][i] else None
                components.append({
                    'id': results['ids'][0][i],
                    'metadata': meta,
                    'distance': results['distances'][0][i],
                    'full_metadata': full_metadata
                })
            logger.debug(f"Found {len(components)} components")

            return components
            
        except Exception as e:
            logger.error(f"Error searching components: {str(e)}")
            raise

    def search_icons(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for icons similar to the query, returning parsed metadata and full document.
        
        Args:
            query: Search query string. Can be icon name, synonym, tag, or use case.
            n_results: Maximum number of results to return.
            
        Returns:
            List of dictionaries containing icon information with the following structure:
            {
                'id': str,
                'metadata': {
                    'component_name': str,
                    'import_statement': str,
                    'description': str,
                    'category': str,
                    'props': Dict,
                    'tags': List[str],
                    'synonyms': List[str],
                    'when_to_use': List[str]
                },
                'distance': float,
                'full_metadata': Dict
            }
        """
        try:
            logger.debug(f"Searching for icons with query: {query}")
            
            # First try exact name match
            exact_query = query.lower().replace("icon", "").strip()
            results = self.collection.get(
                where={"category": "Icon"},
                include=["metadatas", "documents"]
            )
            
            exact_matches = []
            for i, meta in enumerate(results['metadatas']):
                component_name = meta.get('component_name', '').lower()
                if component_name == exact_query or component_name == f"icon{exact_query}":
                    exact_matches.append({
                        'id': results['ids'][i],
                        'metadata': meta,
                        'distance': 0.0,  # Exact match
                        'full_metadata': json.loads(results['documents'][i]) if results['documents'][i] else None
                    })
            
            if exact_matches:
                logger.debug(f"Found exact match for icon: {query}")
                return exact_matches
            
            # If no exact match, try semantic search
            query_embedding = self._create_embedding(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"category": "Icon"}  # Only search in icons
            )
            
            # Format results
            icons = []
            for i in range(len(results['ids'][0])):
                meta = results['metadatas'][0][i]
                
                # Parse fields that are stored as JSON strings
                meta['tags'] = json.loads(meta['tags']) if isinstance(meta['tags'], str) else meta['tags']
                meta['props'] = json.loads(meta['props']) if isinstance(meta['props'], str) else meta['props']
                meta['synonyms'] = json.loads(meta['synonyms']) if isinstance(meta['synonyms'], str) else meta['synonyms']
                meta['when_to_use'] = json.loads(meta['when_to_use']) if isinstance(meta['when_to_use'], str) else meta['when_to_use']
                
                # Add full document
                full_metadata = json.loads(results['documents'][0][i]) if results['documents'][0][i] else None
                
                icons.append({
                    'id': results['ids'][0][i],
                    'metadata': meta,
                    'distance': results['distances'][0][i],
                    'full_metadata': full_metadata
                })
            
            logger.debug(f"Found {len(icons)} icons")
            return icons
            
        except Exception as e:
            logger.error(f"Error searching icons: {str(e)}")
            raise
    
    def delete_component(self, component_id: str) -> None:
        """Delete a component from the vector store."""
        try:
            logger.debug(f"Deleting component with ID: {component_id}")
            self.collection.delete(ids=[component_id])
            logger.debug(f"Successfully deleted component {component_id}")
            
        except Exception as e:
            logger.error(f"Error deleting component: {str(e)}")
            raise

    def clear_collection(self):
        """
        Clear all data from the collection by deleting and recreating it.
        """
        try:
            # Get all IDs from the collection
            results = self.collection.get()
            if results and results['ids']:
                # Delete all documents by their IDs
                self.collection.delete(ids=results['ids'])
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise