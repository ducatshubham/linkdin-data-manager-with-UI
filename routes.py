from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List, Optional, Dict, Any
from bson import ObjectId
from models import Profile, ProfileUpdate, ProfileSearch
from db import get_collection
from etl import import_csv_file, import_folder
import os
import tempfile

router = APIRouter()

@router.post("/profiles/import", response_model=dict)
async def import_profiles(file: UploadFile = File(...), category: Optional[str] = Query(None)):
    """Import profiles from uploaded CSV/Excel file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        result = await import_csv_file(tmp_path, category)
        return {"message": "Import completed", "stats": result}
    finally:
        os.unlink(tmp_path)

@router.post("/profiles/import-folder", response_model=dict)
async def import_profiles_folder(folder_path: str, category: Optional[str] = Query(None)):
    """Import all CSV/Excel files from a folder."""
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="Invalid folder path")
    result = await import_folder(folder_path, category)
    return {"message": "Folder import completed", "stats": result}

@router.get("/profiles", response_model=List[Profile])
async def get_profiles(skip: int = 0, limit: int = 10):
    """Get all profiles with pagination."""
    collection = await get_collection()
    profiles = []
    async for profile in collection.find().skip(skip).limit(limit):
        profiles.append(Profile(**profile))
    return profiles

@router.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile(profile_id: str):
    """Get a single profile by ID."""
    collection = await get_collection()
    profile = await collection.find_one({"_id": ObjectId(profile_id)})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return Profile(**profile)

@router.get("/profiles/search", response_model=List[Profile])
async def search_profiles(
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 10
):
    """Search profiles by filters."""
    collection = await get_collection()
    query = {}
    if role:
        query["current_role"] = {"$regex": role, "$options": "i"}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if skill:
        query["skills"] = {"$in": [skill]}
    if category:
        query["category"] = category

    profiles = []
    async for profile in collection.find(query).skip(skip).limit(limit):
        profiles.append(Profile(**profile))
    return profiles

@router.get("/profiles/by-category", response_model=Dict[str, Dict[str, Any]])
async def get_profiles_by_category(limit: Optional[int] = Query(10, ge=1)):
    """Get profiles grouped by category with counts."""
    collection = await get_collection()
    pipeline = [
        {"$group": {
            "_id": {"$ifNull": ["$category", "Uncategorized"]},
            "profiles": {"$push": "$$ROOT"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$project": {
            "_id": 0,
            "category": "$_id",
            "profiles": {"$slice": ["$profiles", limit]},
            "count": 1
        }}
    ]
    groups = {}
    async for doc in collection.aggregate(pipeline):
        category = doc["category"]
        groups[category] = {
            "profiles": [Profile(**p).dict(by_alias=True) for p in doc["profiles"]],
            "count": doc["count"]
        }
    return groups

@router.put("/profiles/{profile_id}", response_model=Profile)
async def update_profile(profile_id: str, update: ProfileUpdate):
    """Update a profile."""
    collection = await get_collection()
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await collection.update_one({"_id": ObjectId(profile_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    updated_profile = await collection.find_one({"_id": ObjectId(profile_id)})
    return Profile(**updated_profile)

@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile."""
    collection = await get_collection()
    result = await collection.delete_one({"_id": ObjectId(profile_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted"}
