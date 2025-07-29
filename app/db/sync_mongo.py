from pymongo import MongoClient
from app.config import settings

MONGO_URI = settings.MONGO_URI
MONGO_DB_NAME = settings.MONGO_DB_NAME
CLAUSES_COLLECTION_NAME = settings.CLAUSES_COLLECTION_NAME

pymongo_client = MongoClient(MONGO_URI)
pymongo_db = pymongo_client[MONGO_DB_NAME]
clauses_collection = pymongo_db[CLAUSES_COLLECTION_NAME]
