from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from bson import ObjectId
from models import Profile, ProfileUpdate, ProfileSearch
from db import get_collection
from etl import import_csv_file, import_folder
import os
import tempfile
import csv
import io

router = APIRouter()

def _sanitize_profile_document(doc: Dict[str, Any]) -> Profile:
    """Coerce Mongo document into a valid Profile model, filling safe defaults."""
    safe: Dict[str, Any] = {
        "_id": str(doc.get("_id")) if doc.get("_id") else None,
        "profile_id": doc.get("profile_id", ""),
        "name": doc.get("name", ""),
        "current_role": doc.get("current_role", ""),
        "current_company": doc.get("current_company", ""),
        "location": doc.get("location", ""),
        "skills": doc.get("skills", []) or [],
        "experience": doc.get("experience", []) or [],
        "education": doc.get("education", []) or [],
        "profile_url": doc.get("profile_url", ""),
        "category": doc.get("category"),
        "raw_json": doc.get("raw_json", {}),
    }
    return Profile(**safe)

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
    async for profile in collection.find().sort("last_scraped_at", -1).skip(skip).limit(limit):
        try:
            profiles.append(_sanitize_profile_document(profile))
        except Exception:
            # Skip malformed documents instead of failing the whole request
            continue
    return profiles

@router.get("/profiles/by-id/{profile_id}", response_model=Profile)
async def get_profile(profile_id: str):
    """Get a single profile by ID."""
    collection = await get_collection()
    # Since _id is stored as string in the database, query directly by string
    profile = await collection.find_one({"_id": profile_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _sanitize_profile_document(profile)

@router.get("/profiles/search", response_model=List[Profile])
async def search_profiles(
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Global search across name/role/company/location/skills"),
    skip: int = 0,
    limit: int = 10
):
    """Search profiles by filters."""
    collection = await get_collection()
    criteria = []
    if role:
        criteria.append({"current_role": {"$regex": role, "$options": "i"}})
    if location:
        criteria.append({"location": {"$regex": location, "$options": "i"}})
    if skill:
        # For arrays of strings, regex directly on field works across elements
        criteria.append({"skills": {"$regex": skill, "$options": "i"}})
    if category:
        criteria.append({"category": category})
    if q:
        or_block = {
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"current_role": {"$regex": q, "$options": "i"}},
                {"current_company": {"$regex": q, "$options": "i"}},
                {"location": {"$regex": q, "$options": "i"}},
                {"skills": {"$regex": q, "$options": "i"}},
                {"category": {"$regex": q, "$options": "i"}},
            ]
        }
        criteria.append(or_block)

    query = {"$and": criteria} if criteria else {}

    profiles = []
    async for profile in collection.find(query).sort("last_scraped_at", -1).skip(skip).limit(limit):
        try:
            profiles.append(_sanitize_profile_document(profile))
        except Exception:
            continue
    return profiles

@router.get("/profiles/search-adv", response_model=Dict[str, Any])
async def search_profiles_advanced(
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 10
):
    """Search returning items and total count for pagination UI."""
    collection = await get_collection()
    criteria = []
    if role:
        criteria.append({"current_role": {"$regex": role, "$options": "i"}})
    if location:
        criteria.append({"location": {"$regex": location, "$options": "i"}})
    if skill:
        criteria.append({"skills": {"$elemMatch": {"$regex": skill, "$options": "i"}}})
    if category:
        criteria.append({"category": category})
    if q:
        criteria.append({
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"current_role": {"$regex": q, "$options": "i"}},
                {"current_company": {"$regex": q, "$options": "i"}},
                {"location": {"$regex": q, "$options": "i"}},
                {"skills": {"$regex": q, "$options": "i"}},
                {"category": {"$regex": q, "$options": "i"}},
                {"education": {"$elemMatch": {"institute": {"$regex": q, "$options": "i"}}}},
            ]
        })
    query = {"$and": criteria} if criteria else {}

    total = await collection.count_documents(query)
    items: List[Profile] = []
    async for doc in collection.find(query).sort("last_scraped_at", -1).skip(skip).limit(limit):
        try:
            items.append(_sanitize_profile_document(doc))
        except Exception:
            continue
    return {"items": items, "total": total}

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

@router.put("/profiles/by-id/{profile_id}", response_model=Profile)
async def update_profile(profile_id: str, update: ProfileUpdate):
    """Update a profile."""
    collection = await get_collection()
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await collection.update_one({"_id": profile_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    updated_profile = await collection.find_one({"_id": profile_id})
    return _sanitize_profile_document(updated_profile)

@router.delete("/profiles/by-id/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile."""
    collection = await get_collection()
    result = await collection.delete_one({"_id": profile_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted"}

@router.get("/profiles/export-csv")
async def export_profiles_csv(
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    """Export profiles to CSV based on filters."""
    collection = await get_collection()
    criteria = []
    if role:
        criteria.append({"current_role": {"$regex": role, "$options": "i"}})
    if location:
        criteria.append({"location": {"$regex": location, "$options": "i"}})
    if skill:
        criteria.append({"skills": {"$elemMatch": {"$regex": skill, "$options": "i"}}})
    if category:
        criteria.append({"category": category})
    if q:
        criteria.append({
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"current_role": {"$regex": q, "$options": "i"}},
                {"current_company": {"$regex": q, "$options": "i"}},
                {"location": {"$regex": q, "$options": "i"}},
                {"skills": {"$regex": q, "$options": "i"}},
                {"category": {"$regex": q, "$options": "i"}},
                {"education": {"$elemMatch": {"institute": {"$regex": q, "$options": "i"}}}},
            ]
        })
    query = {"$and": criteria} if criteria else {}

    # Fetch all matching profiles
    profiles = []
    async for doc in collection.find(query).sort("last_scraped_at", -1):
        try:
            profiles.append(_sanitize_profile_document(doc))
        except Exception:
            continue

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Profile ID", "Name", "Current Role", "Current Company", "Location",
        "Skills", "Experience", "Education", "Profile URL", "Category"
    ])

    # Rows
    for p in profiles:
        writer.writerow([
            p.profile_id,
            p.name,
            p.current_role,
            p.current_company,
            p.location,
            "; ".join(p.skills),
            "; ".join([f"{e.role} at {e.company}" for e in p.experience]),
            "; ".join([f"{e.degree} from {e.institute}" for e in p.education]),
            p.profile_url,
            p.category or "",
        ])

    output.seek(0)
    response = StreamingResponse(io.StringIO(output.getvalue()), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=profiles_export.csv"
    return response

@router.get("/profiles/stats", response_model=Dict[str, Any])
async def get_profiles_stats():
    """Get basic stats about profiles."""
    collection = await get_collection()
    total = await collection.count_documents({})
    return {"total_profiles": total}

@router.post("/profiles/backfill-education")
async def backfill_education():
    """One-time helper: if education is empty but raw_json has 'Education', fill it."""
    collection = await get_collection()
    updated = 0
    async for doc in collection.find({"$or": [{"education": {"$size": 0}}, {"education": {"$exists": False}}]}):
        raw = doc.get("raw_json", {})
        edu = raw.get("Education") or raw.get("education")
        if not edu:
            continue
        if isinstance(edu, list):
            edu_list = [{"degree": "", "institute": str(e).strip()} for e in edu if str(e).strip()]
        else:
            edu_list = [{"degree": "", "institute": s.strip()} for s in str(edu).split("|") if s.strip()]
        if edu_list:
            await collection.update_one({"_id": doc["_id"]}, {"$set": {"education": edu_list}})
            updated += 1
    return {"updated": updated}

@router.post("/profiles/detect-company/{profile_id}")
async def detect_company_for_profile(profile_id: str):
    """Detect current company for a specific profile using AI."""
    from utils import detect_current_company
    collection = await get_collection()
    profile = await collection.find_one({"_id": profile_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.get("current_company"):
        return {"message": "Current company already set", "current_company": profile["current_company"]}
    detected = detect_current_company(profile)
    if detected:
        await collection.update_one({"_id": profile_id}, {"$set": {"current_company": detected}})
        return {"message": "Company detected and updated", "current_company": detected}
    return {"message": "Could not detect company"}
