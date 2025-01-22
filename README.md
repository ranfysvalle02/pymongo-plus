# pymongo-plus

---

```
from pymongo import *  # Import everything from the original pymongo module
from pymongo import MongoClient as RealMongoClient  # Import the real MongoClient

# Custom MongoClient wrapper
class MongoClient(RealMongoClient):
    def __init__(self, *args, **kwargs):
        """
        Extend the original MongoClient initialization.
        Pass all arguments to the real MongoClient.
        """
        super().__init__(*args, **kwargs)

    def get_database_names(self):
        """Custom method: Get a list of all database names."""
        return self.list_database_names()

    def get_collection_names(self, database_name):
        """Custom method: Get a list of all collection names in a database."""
        database = self[database_name]
        return database.list_collection_names()

    # Add any other truly custom functionality here as needed


# Re-export everything from pymongo and replace MongoClient
__all__ = [name for name in dir() if not name.startswith("_")]


if __name__ == "__main__":
    # Create an instance of the custom MongoClient
    client = MongoClient("mongodb://0.0.0.0/?directConnection=true")
    # Demo: Get a list of all database names
    print("Databases:", client.get_database_names())
    # Demo: Get a list of all collection names in a specific database
    database_name = "test_database"
    print(f"Collections in '{database_name}':", client.get_collection_names(database_name))

"""
docker run -d -p 27017:27017 --restart unless-stopped mongodb/mongodb-atlas-local
"""
```
