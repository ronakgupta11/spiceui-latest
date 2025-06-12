
from opensearchpy import OpenSearch, exceptions
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class AWSComponentVectorStore:
    def __init__(self):
        self.client = OpenSearch(
            hosts=[{'host': 'search-spiceui-vectorstore-lnuytstobyg4b25dvnpxzln4wy.aos.us-east-1.on.aws', 'port': 443}],
            http_auth=('spiceui-admin', 'Pwd@spiceui#vectordb123'),
            use_ssl=True,
            verify_certs=True
        )
        self.index = "components"
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._ensure_index()

    def _ensure_index(self):
        """Create index if it doesn't exist with the proper KNN settings and mappings."""
        try:
            if not self.client.indices.exists(index=self.index):
                logger.info(f"Index '{self.index}' does not exist. Creating it...")
                index_config = {
                    "settings": {
                        "index": {
                            "knn": True
                        }
                    },
                    "mappings": {
                        "properties": {
                            "name": {"type": "text"},
                            "description": {"type": "text"},
                            "props": {"type": "text"},
                            "examples": {"type": "text"},
                            "category": {"type": "keyword"},
                            "tags": {"type": "text"},
                            "embedding": {
                                "type": "knn_vector",
                                "dimension": 384  # for MiniLM
                            }
                        }
                    }
                }
                self.client.indices.create(index=self.index, body=index_config)
                logger.info(f"Index '{self.index}' created successfully.")
            else:
                logger.debug(f"Index '{self.index}' already exists.")
        except exceptions.OpenSearchException as e:
            logger.error(f"Error checking/creating index: {str(e)}")
            raise

    def _create_embedding(self, text: str) -> List[float]:
        return self.embedding_model.encode(text).tolist()

    def add_component(self, component_id: str, metadata: Dict[str, Any]):
        text = f"{metadata['name']} {metadata['description']} {' '.join(metadata['tags'])}"
        embedding = self._create_embedding(text)
        document = {
            "name": metadata["name"],
            "description": metadata["description"],
            "props": json.dumps(metadata["props"]),
            "examples": json.dumps(metadata["examples"]),
            "category": metadata.get("category", ""),
            "tags": " ".join(metadata["tags"]),
            "embedding": embedding
        }
        self.client.index(index=self.index, id=component_id, body=document)

    def get_component(self, component_id: str) -> Dict[str, Any]:
        res = self.client.get(index=self.index, id=component_id)
        source = res["_source"]
        return {
            "id": res["_id"],
            "metadata": {
                "name": source["name"],
                "description": source["description"],
                "props": json.loads(source["props"]),
                "examples": json.loads(source["examples"]),
                "category": source["category"],
                "tags": source["tags"].split()
            },
            "document": source
        }

    def search_components(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self._create_embedding(query)
        search_query = {
            "size": n_results,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": n_results
                    }
                }
            }
        }
        res = self.client.search(index=self.index, body=search_query)
        return [
            {
                "id": hit["_id"],
                "metadata": hit["_source"],
                "distance": hit["_score"]
            }
            for hit in res["hits"]["hits"]
        ]

    def delete_component(self, component_id: str):
        self.client.delete(index=self.index, id=component_id)
