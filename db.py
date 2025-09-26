import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

load_dotenv()

MONGODB_URI = "mongodb+srv://kunwarshubham78:singhshubham90742@pymongo.j4df9k2.mongodb.net/?retryWrites=true&w=majority&appName=pymongo"
DATABASE_NAME = os.getenv("DATABASE_NAME", "linkedin_data")

client = AsyncIOMotorClient(MONGODB_URI)
database = client[DATABASE_NAME]
collection = database["profiles"]

async def get_collection():
    return collection

async def create_indexes():
    """Create required indexes on the collection."""
    await collection.create_index("profile_url", unique=True)
    await collection.create_index("current_role")
    await collection.create_index("skills")
    await collection.create_index("location")
    await collection.create_index("category")

# Call this on startup
# import asyncio
# asyncio.create_task(create_indexes())
