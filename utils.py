import re
from typing import List, Dict, Any
import uuid
import pandas as pd

def clean_string(value) -> str:
    """Trim spaces and normalize string."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()

def normalize_company_name(company: str) -> str:
    """Normalize company names by removing common suffixes and standardizing."""
    company = clean_string(company).lower()
    # Remove common suffixes
    company = re.sub(r'\s+(inc|llc|ltd|corp|corporation|company|co\.?|ltd\.?|inc\.?|llc\.?)$', '', company)
    return company.title()

def parse_skills(skills_str: str) -> List[str]:
    """Convert skills string to list, split by comma or semicolon."""
    if not skills_str:
        return []
    skills = re.split(r'[;,]', skills_str)
    return [clean_string(skill) for skill in skills if skill.strip()]

def standardize_date(date_str: str) -> str:
    """Standardize date format. For now, just clean it."""
    return clean_string(date_str)

def generate_profile_id(url: str) -> str:
    """Generate a unique profile_id from URL or UUID."""
    if url:
        # Extract profile ID from LinkedIn URL
        match = re.search(r'/in/([^/?]+)', url)
        if match:
            return match.group(1)
    return str(uuid.uuid4())

def deduplicate_profiles(profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates based on profile_url."""
    seen_urls = set()
    unique_profiles = []
    for profile in profiles:
        url = profile.get('profile_url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_profiles.append(profile)
    return unique_profiles

def clean_profile_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and transform raw profile data."""
    cleaned = {}
    cleaned['profile_id'] = generate_profile_id(clean_string(raw_data.get('profile_url', '')))
    cleaned['name'] = clean_string(raw_data.get('name', ''))
    cleaned['current_role'] = clean_string(raw_data.get('current_role', ''))
    cleaned['current_company'] = normalize_company_name(clean_string(raw_data.get('current_company', '')))
    cleaned['location'] = clean_string(raw_data.get('location', ''))
    cleaned['skills'] = parse_skills(clean_string(raw_data.get('skills', '')))
    cleaned['experience'] = []  # Assuming experience is parsed separately
    cleaned['education'] = []  # Assuming education is parsed separately
    cleaned['profile_url'] = clean_string(raw_data.get('profile_url', ''))
    cleaned['raw_json'] = raw_data
    return cleaned
