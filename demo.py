from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.operations import SearchIndexModel
import logging
import time
from pymongo.errors import OperationFailure


# Get Embedding Function
import openai
from typing import List
def get_embedding(text: str, model: str = "text-embedding-3-small", dimensions: int = 256) -> List[float]:
    text = text.replace("\n", " ")
    try:
        return openai.OpenAI().embeddings.create(input=[text], model=model, dimensions=dimensions).data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Custom MongoClient wrapper
class PymongoPlus(MongoClient):
    def __init__(self, *args, **kwargs):
        """
        Extend the original MongoClient initialization.
        Pass all arguments to the real MongoClient.
        """
        super().__init__(*args, **kwargs)

    def create_if_not_exists(self, database_name: str, collection_name: str) -> Collection:
        """
        Ensure the collection exists. Create it if it does not.
        :param database_name: The database name.
        :param collection_name: The collection name.
        :return: The collection object.
        """
        database = self[database_name]
        collection_names = database.list_collection_names()

        if collection_name not in collection_names:
            logger.info(f"Collection '{collection_name}' does not exist. Creating it now.")
            # Create the collection by accessing it and optionally inserting a dummy document
            collection = database[collection_name]
            collection.insert_one({"_id": 0, "placeholder": True})
            collection.delete_one({"_id": 0})  # Remove the placeholder document
            logger.info(f"Collection '{collection_name}' created successfully.")
        else:
            collection = database[collection_name]

        return collection

    def _create_search_index(
        self,
        database_name: str,
        collection_name: str,
        index_name: str,
        # get_embedding should be a function that returns the embedding for a document
        get_embedding: callable,
        distance_metric: str = "euclidean",
    ) -> None:
        """
        Create the Atlas Search index for vector search.
        :param database_name: The database where the collection resides.
        :param collection_name: The collection for which to create the search index.
        :param index_name: The name of the search index.
        :param num_dimensions: The number of dimensions for the vector search.
        :param distance_metric: The distance metric for similarity (default: 'euclidean').
        """
        try:
            # Ensure the collection exists
            self.create_if_not_exists(database_name, collection_name)

            # Check if the index already exists
            if self.index_exists(database_name, collection_name, index_name):
                logger.info(f"Search index '{index_name}' already exists in collection '{collection_name}'.")
                return

            logger.info(f"Creating search index '{index_name}' for collection '{collection_name}'.")

            # Build the search index model
            search_index_model = SearchIndexModel(
                definition={
                    "fields": [
                        {
                            "type": "vector",
                            "numDimensions": len(get_embedding("0")),
                            "path": "embedding",
                            "similarity": distance_metric,
                        },
                    ]
                },
                name=index_name,
                type="vectorSearch",
            )

            # Access the specified collection
            collection = self[database_name][collection_name]

            # Create the Atlas Search index
            collection.create_search_index(model=search_index_model)
            logger.info(f"Search index '{index_name}' created successfully for collection '{collection_name}'.")

        except OperationFailure as e:
            logger.error(f"Operation failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to create search index '{index_name}': {e}")
            raise e
    def search(
        self, query: str, limit: int = 5, database_name:str = "", collection_name:str = "", index_name: str = "", filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search the MongoDB collection for documents relevant to the query."""
        query_embedding = get_embedding(query)
        if not self.index_exists(database_name, collection_name, index_name):
            logger.error(f"Index {index_name} does not exist.")
            return []
        if query_embedding is None:
            logger.error(f"Failed to generate embedding for query: {query}")
            return []

        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": index_name,
                        "limit": 10,
                        "numCandidates": 10,
                        "queryVector": self.embedder.get_embedding(query),
                        "path": "embedding",
                    }
                },
                {"$set": {"score": {"$meta": "vectorSearchScore"}}},
            ]
            pipeline.append({"$project": {"embedding": 0}})
            agg = list(self._collection.aggregate(pipeline))
            docs = []
            for doc in agg:
                docs.append(
                    Document(
                        id=str(doc["_id"]),
                        name=doc.get("name"),
                        content=doc["content"],
                        meta_data=doc.get("meta_data", {}),
                    )
                )
            logger.info(f"Search completed. Found {len(docs)} documents.")
            return docs
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    def index_exists(self, database_name: str, collection_name: str, index_name: str) -> bool:
        """
        Check if the search index exists.
        :param database_name: The database where the collection resides.
        :param collection_name: The collection to check.
        :param index_name: The name of the search index to check.
        :return: True if the index exists, False otherwise.
        """
        try:
            collection = self[database_name][collection_name]
            indexes = list(collection.list_search_indexes())
            exists = any(index["name"] == index_name for index in indexes)
            return exists
        except OperationFailure as e:
            logger.error(f"Operation failure while checking index existence: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking search index existence for '{index_name}': {e}")
            return False


if __name__ == "__main__":
    # Create an instance of the custom MongoClient
    client = PymongoPlus("mongodb://0.0.0.0/?directConnection=true")

    # Define parameters for the demo
    database_name = "test_database"
    collection_name = "test_collection"
    index_name = "vector_search_index"
    distance_metric = "cosine"

    # Step 1: Attempt to create the index
    client._create_search_index(
        database_name=database_name,
        collection_name=collection_name,
        index_name=index_name,
        get_embedding=get_embedding,
        distance_metric=distance_metric,
    )

    # Step 2: Wait for the index to be created
    logger.info("Waiting for the search index to be available...")
    max_attempts = 10  # Maximum number of attempts to check
    attempt = 0
    while not client.index_exists(database_name, collection_name, index_name):
        attempt += 1
        if attempt > max_attempts:
            logger.error("Search index creation timed out after waiting.")
            break
        logger.info(f"Attempt {attempt}: Search index '{index_name}' not ready yet. Waiting...")
        time.sleep(1)  # Wait for 1 second before checking again

    # Step 3: Check final status 
    if client.index_exists(database_name, collection_name, index_name):
        logger.info(f"Search index '{index_name}' is now available!")
        print("Index is ready!")
    else:
        print("Index creation process exceeded wait limit.")
