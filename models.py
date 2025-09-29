from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from bson import ObjectId

class Experience(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class Education(BaseModel):
    degree: str
    institute: str
    year: Optional[int] = None

class Profile(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    profile_id: str
    name: str
    current_role: str
    current_company: str
    location: str
    skills: List[str] = []
    experience: List[Experience] = []
    education: List[Education] = []
    total_experience: Optional[str] = None
    profile_url: str
    category: Optional[str] = None
    last_scraped_at: datetime = Field(default_factory=datetime.utcnow)
    raw_json: Dict = {}

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    current_role: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[Experience]] = None
    education: Optional[List[Education]] = None
    profile_url: Optional[str] = None
    raw_json: Optional[Dict] = None

class ProfileSearch(BaseModel):
    role: Optional[str] = None
    location: Optional[str] = None
    skill: Optional[str] = None
    category: Optional[str] = None
