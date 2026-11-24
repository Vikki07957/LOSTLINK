"""
LOSTLINK - MongoDB Database Layer
Connects to MongoDB Atlas via PyMongo.
Includes an intelligent embedded JSON fallback engine for offline viva demonstrations
and environments without active internet connectivity.
"""

import os
import json
import logging
from datetime import datetime, timezone
from bson import ObjectId
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LOSTLINK_DB")

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle BSON ObjectId and datetime objects."""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

class EmbeddedCursor:
    """Mock PyMongo Cursor with sort, skip, and limit support."""
    def __init__(self, items):
        self._items = list(items)

    def sort(self, key_or_list, direction=pymongo.ASCENDING):
        if isinstance(key_or_list, list):
            for key, direct in reversed(key_or_list):
                reverse = (direct == pymongo.DESCENDING or direct == -1)
                self._items.sort(key=lambda x: (x.get(key) is None, x.get(key)), reverse=reverse)
        else:
            key = key_or_list
            reverse = (direction == pymongo.DESCENDING or direction == -1)
            self._items.sort(key=lambda x: (x.get(key) is None, x.get(key)), reverse=reverse)
        return self

    def skip(self, n):
        self._items = self._items[n:]
        return self

    def limit(self, n):
        if n > 0:
            self._items = self._items[:n]
        return self

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

class EmbeddedCollection:
    """Embedded JSON Collection mimicking PyMongo Collection interface."""
    def __init__(self, db, name):
        self.db = db
        self.name = name

    def _matches_filter(self, doc, filter_dict):
        if not filter_dict:
            return True
        for key, expected in filter_dict.items():
            if key == "_id":
                doc_id = str(doc.get("_id", ""))
                exp_id = str(expected)
                if doc_id != exp_id:
                    return False
            elif key == "$or":
                sub_match = any(self._matches_filter(doc, sub) for sub in expected)
                if not sub_match:
                    return False
            elif isinstance(expected, dict):
                val = doc.get(key)
                if "$regex" in expected:
                    import re
                    pattern = expected["$regex"]
                    options = expected.get("$options", "")
                    flags = re.IGNORECASE if "i" in options else 0
                    if not (isinstance(val, str) and re.search(pattern, val, flags)):
                        return False
                elif "$in" in expected:
                    if val not in expected["$in"]:
                        return False
                elif "$nin" in expected:
                    if val in expected["$nin"]:
                        return False
                elif "$ne" in expected:
                    if val == expected["$ne"]:
                        return False
            else:
                if doc.get(key) != expected:
                    return False
        return True

    def find(self, filter_dict=None, projection=None):
        docs = self.db._get_collection_data(self.name)
        matched = [dict(d) for d in docs if self._matches_filter(d, filter_dict)]
        return EmbeddedCursor(matched)

    def find_one(self, filter_dict=None, projection=None):
        docs = self.db._get_collection_data(self.name)
        for d in docs:
            if self._matches_filter(d, filter_dict):
                return dict(d)
        return None

    def insert_one(self, doc):
        docs = self.db._get_collection_data(self.name)
        inserted_doc = dict(doc)
        if "_id" not in inserted_doc:
            inserted_doc["_id"] = ObjectId()
        elif isinstance(inserted_doc["_id"], str):
            try:
                inserted_doc["_id"] = ObjectId(inserted_doc["_id"])
            except Exception:
                pass
        docs.append(inserted_doc)
        self.db._save_data()
        
        class InsertResult:
            def __init__(self, id_val):
                self.inserted_id = id_val
        return InsertResult(inserted_doc["_id"])

    def update_one(self, filter_dict, update_dict):
        docs = self.db._get_collection_data(self.name)
        modified_count = 0
        for i, d in enumerate(docs):
            if self._matches_filter(d, filter_dict):
                if "$set" in update_dict:
                    for k, v in update_dict["$set"].items():
                        docs[i][k] = v
                else:
                    docs[i].update(update_dict)
                modified_count += 1
                break
        if modified_count > 0:
            self.db._save_data()
        
        class UpdateResult:
            def __init__(self, count):
                self.modified_count = count
        return UpdateResult(modified_count)

    def delete_one(self, filter_dict):
        docs = self.db._get_collection_data(self.name)
        deleted_count = 0
        for i, d in enumerate(docs):
            if self._matches_filter(d, filter_dict):
                del docs[i]
                deleted_count = 1
                break
        if deleted_count > 0:
            self.db._save_data()

        class DeleteResult:
            def __init__(self, count):
                self.deleted_count = count
        return DeleteResult(deleted_count)

    def count_documents(self, filter_dict=None):
        docs = self.db._get_collection_data(self.name)
        if not filter_dict:
            return len(docs)
        return sum(1 for d in docs if self._matches_filter(d, filter_dict))

    def distinct(self, key, filter_dict=None):
        docs = self.db._get_collection_data(self.name)
        values = set()
        for d in docs:
            if self._matches_filter(d, filter_dict) and key in d:
                values.add(d[key])
        return list(values)

class EmbeddedDatabase:
    """Local JSON-persisted database for offline demonstration / viva."""
    def __init__(self, filepath=None):
        if filepath is None:
            data_dir = os.path.join(Config.BASE_DIR, "data")
            os.makedirs(data_dir, exist_ok=True)
            filepath = os.path.join(data_dir, "lostlink_local.json")
        self.filepath = filepath
        self.data = self._load_data()
        self.name = Config.DB_NAME

    def _load_data(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    # Convert _id strings back to ObjectId
                    for col in raw.values():
                        for doc in col:
                            if "_id" in doc and isinstance(doc["_id"], str):
                                try:
                                    doc["_id"] = ObjectId(doc["_id"])
                                except Exception:
                                    pass
                    return raw
            except Exception as e:
                logger.warning(f"Could not load local database file: {e}")
        return {"users": [], "items": [], "claims": [], "activity_logs": [], "categories": []}

    def _save_data(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, cls=JSONEncoder)
        except Exception as e:
            logger.error(f"Error saving local database: {e}")

    def _get_collection_data(self, col_name):
        if col_name not in self.data:
            self.data[col_name] = []
        return self.data[col_name]

    def __getitem__(self, name):
        return EmbeddedCollection(self, name)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return self[name]

    def list_collection_names(self):
        return list(self.data.keys())

class DatabaseManager:
    """Manages connection to MongoDB Atlas and provides fail-safe fallback."""
    _instance = None

    def __init__(self):
        self.client = None
        self.db = None
        self.is_atlas = False
        self.status_message = "Initializing..."
        self._initialize()

    def _initialize(self):
        uri = Config.MONGODB_URI.strip() if Config.MONGODB_URI else ""
        
        # Check if a valid MongoDB Atlas URI is present
        if uri and ("mongodb+srv://" in uri or "mongodb://" in uri) and "<username>" not in uri and "<password>" not in uri:
            try:
                logger.info("Attempting connection to MongoDB Atlas...")
                # Connect with a reasonable timeout for viva/production
                self.client = pymongo.MongoClient(
                    uri,
                    serverSelectionTimeoutMS=3000,
                    connectTimeoutMS=3000,
                    socketTimeoutMS=5000,
                    tlsAllowInvalidCertificates=True
                )
                # Verify server ping
                self.client.admin.command('ping')
                self.db = self.client[Config.DB_NAME]
                self.is_atlas = True
                self.status_message = "MongoDB Atlas Connected"
                logger.info(f"SUCCESS: Connected to MongoDB Atlas ({Config.DB_NAME})")
                return
            except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
                logger.warning(f"Could not connect to MongoDB Atlas ({e}). Activating embedded demo engine.")
                self.is_atlas = False
                self.client = None
        else:
            logger.info("No active MongoDB Atlas URI provided. Running in embedded viva demonstration mode.")

        # Activate embedded MongoDB engine
        self.is_atlas = False
        self.db = EmbeddedDatabase()
        self.status_message = "Embedded Mock Database (Viva Demo Ready)"

    def get_db(self):
        if self.db is None:
            self._initialize()
        return self.db

    def get_status(self):
        return {
            "is_atlas": self.is_atlas,
            "status_message": self.status_message,
            "db_name": Config.DB_NAME,
            "engine": "MongoDB Atlas (PyMongo)" if self.is_atlas else "Embedded PyMongo-Compatible Store"
        }

# Singleton instance
db_manager = DatabaseManager()

def get_db():
    """Retrieve active database instance (Atlas or Embedded)."""
    return db_manager.get_db()

def get_db_status():
    """Retrieve connection diagnostic status."""
    return db_manager.get_status()

def to_object_id(id_val):
    """Safely convert string or ObjectId into ObjectId."""
    if isinstance(id_val, ObjectId):
        return id_val
    try:
        return ObjectId(str(id_val))
    except Exception:
        return None

def serialize_doc(doc):
    """Format MongoDB doc to be JSON and template-safe."""
    if not doc:
        return None
    res = dict(doc)
    if "_id" in res:
        res["id"] = str(res["_id"])
        res["_id"] = str(res["_id"])
    return res

def serialize_docs(docs):
    """Format list of MongoDB docs."""
    return [serialize_doc(d) for d in docs if d]
