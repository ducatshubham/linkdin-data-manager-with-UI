import pandas as pd
import os
import logging
import re
from typing import List, Dict, Any
from datetime import datetime
from db import get_collection
from utils import clean_profile_data, deduplicate_profiles
from models import Profile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def import_csv_file(file_path: str, category: str = None) -> Dict[str, int]:
    """Import data from a single CSV/Excel file."""
    collection = await get_collection()
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")

    raw_profiles = df.to_dict('records')
    # Map CSV columns to model keys using MAPPING_TEMPLATE
    mapped_profiles = []
    for row in raw_profiles:
        mapped = {}
        for csv_key, model_key in MAPPING_TEMPLATE.items():
            if csv_key in row:
                mapped[model_key] = row[csv_key]
        mapped_profiles.append(mapped)
    cleaned_profiles = [clean_profile_data(row) for row in mapped_profiles]
    unique_profiles = deduplicate_profiles(cleaned_profiles)

    inserted = 0
    updated = 0
    skipped = 0

    for profile_data in unique_profiles:
        if category:
            profile_data['category'] = category
        # Detect current company if not present or empty
        if not profile_data.get('current_company'):
            from utils import detect_current_company
            detected_company = detect_current_company(profile_data)
            if detected_company:
                profile_data['current_company'] = detected_company
        profile_url = profile_data['profile_url']
        existing = await collection.find_one({"profile_url": profile_url})
        if existing:
            # Update existing
            await collection.update_one({"profile_url": profile_url}, {"$set": profile_data})
            updated += 1
        else:
            # Insert new
            profile = Profile(**profile_data)
            await collection.insert_one(profile.dict(by_alias=True))
            inserted += 1

    logger.info(f"Imported {file_path} with category '{category}': inserted={inserted}, updated={updated}, skipped={skipped}")
    result = {"inserted": inserted, "updated": updated, "skipped": skipped}
    if category:
        result["category"] = category
    return result

async def import_folder(folder_path: str, category: str = None) -> Dict[str, Dict[str, int]]:
    """Import all CSV/Excel files in a folder."""
    results = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith(('.csv', '.xlsx', '.xls')):
            file_path = os.path.join(folder_path, file_name)
            file_category = category
            if not file_category:
                # Auto-detect category from filename, e.g., "linkedin_senior_software_engineer_results.csv" -> "senior_software_engineer"
                match = re.search(r'^linkedin_(.+?)_results\.(csv|xlsx|xls)$', file_name, re.IGNORECASE)
                if match:
                    file_category = match.group(1).replace('_', ' ').title()  # e.g., "Senior Software Engineer"
            results[file_name] = await import_csv_file(file_path, file_category)
    return results

# Mapping template (example)
MAPPING_TEMPLATE = {
    "Name": "name",
    "Current Role": "current_role",
    "Title": "current_role",
    "Current Company": "current_company",
    # Company is optional in new sheet; omit mapping so it doesn't override with empty
    "Location": "location",
    "Education": "education",
    "Experience Details": "experience",
    "Total Experience": "total_experience",
    "Skills": "skills",
    "Profile URL": "profile_url",
    # Add more mappings as needed
}
