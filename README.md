# pymongo-plus

---

### Blog Draft: **Extending MongoDB with a Custom MongoClient Wrapper**

---

#### **Introduction**
MongoDB's flexibility and PyMongo's robust driver make it a popular choice for database management in Python applications. While PyMongo's `MongoClient` class provides rich functionality, there are scenarios where adding custom methods can simplify repetitive tasks or enhance the developer experience. In this blog post, we’ll explore how to create a custom `MongoClient` wrapper that extends the default behavior, complete with practical examples.

---

#### **1. Why Customize MongoClient?**
- **Streamlined Operations**: Simplify frequent tasks like listing databases and collections.
- **Encapsulation**: Abstract additional functionality into a single, reusable class.
- **Extensibility**: Add new methods to tailor MongoDB operations to your project’s needs.

---

#### **2. Setting Up the Environment**
Before diving into code, we’ll need a MongoDB instance to work with. A simple command to start a local MongoDB container:

```bash
docker run -d -p 27017:27017 --restart unless-stopped mongodb/mongodb-atlas-local
```

---

#### **3. The Custom MongoClient**
We build a custom `MongoClient` class by inheriting from PyMongo’s original `MongoClient`. The class adds two convenient methods:
- `get_database_names()`: Fetch all database names.
- `get_collection_names(database_name)`: Fetch all collection names for a given database.

Here’s the complete implementation:

```python
from pymongo import *  # Import everything from the original pymongo module
from pymongo import MongoClient as RealMongoClient  # Import the real MongoClient

class MongoClient(RealMongoClient):
    def __init__(self, *args, **kwargs):
        """Extend the original MongoClient initialization."""
        super().__init__(*args, **kwargs)

    def get_database_names(self):
        """Custom method: Get a list of all database names."""
        return self.list_database_names()

    def get_collection_names(self, database_name):
        """Custom method: Get a list of all collection names in a database."""
        database = self[database_name]
        return database.list_collection_names()
```

---

#### **4. Using the Custom MongoClient**
Let’s see the custom methods in action:

```python
if __name__ == "__main__":
    # Create an instance of the custom MongoClient
    client = MongoClient("mongodb://0.0.0.0/?directConnection=true")
    
    # Get a list of all database names
    print("Databases:", client.get_database_names())
    
    # Get a list of all collection names in a specific database
    database_name = "test_database"
    print(f"Collections in '{database_name}':", client.get_collection_names(database_name))
```

---

#### **5. Key Benefits of the Wrapper**
- **Enhanced Readability**: Method names like `get_database_names` are more intuitive for developers unfamiliar with PyMongo’s `list_database_names`.
- **Ease of Extension**: Add methods specific to your project’s requirements without modifying the original `MongoClient`.

---

#### **6. Next Steps**
- **Add More Custom Methods**: Extend the wrapper with additional methods, such as database statistics or querying utilities.
- **Integrate with Applications**: Replace instances of `MongoClient` in your projects with the custom wrapper for enhanced functionality.

---

#### **Conclusion**
Creating a custom MongoDB client wrapper is a simple yet powerful way to extend PyMongo’s capabilities. By abstracting common tasks and adding custom methods, you can streamline development workflows and make your codebase more maintainable. Try extending the wrapper with your own methods tailored to your unique needs!

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
