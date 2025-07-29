from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

MONGO_URI = settings.MONGO_URI
MONGO_DB_NAME = settings.MONGO_DB_NAME
CLAUSES_COLLECTION_NAME = settings.CLAUSES_COLLECTION_NAME

motor_client = AsyncIOMotorClient(MONGO_URI)
motor_db = motor_client[MONGO_DB_NAME]
clauses_collection = motor_db[CLAUSES_COLLECTION_NAME]
# TODO: Create indexes for faster queries
