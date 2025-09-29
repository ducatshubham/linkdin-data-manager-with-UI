# LinkedIn Data Manager

A complete FastAPI project for managing LinkedIn scraped data stored in MongoDB. Supports ETL for importing from Excel/CSV files and provides CRUD API endpoints with search/filter capabilities.

## Project Structure
```
linkedin_data_manager/
├── main.py              # FastAPI app entry point
├── models.py            # Pydantic models for Profile
├── db.py                # MongoDB connection and indexes
├── utils.py             # Data cleaning and utility functions
├── etl.py               # ETL pipeline for importing data
├── routes.py            # API endpoints
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── example.csv          # Sample data file
└── README.md            # This file
```

## Setup Instructions

1. **Clone or Create Project**
   - The project is already set up in `linkedin_data_manager` folder.

2. **Install Dependencies**
   ```
   cd linkedin_data_manager
   pip install -r requirements.txt
   ```

3. **Set Up Environment**
   - Copy `.env.example` to `.env` and update `MONGODB_URI` with your MongoDB connection string.
   - Example for local MongoDB:
     ```
     MONGODB_URI=mongodb://localhost:27017
     DATABASE_NAME=linkedin_data
     ```
   - For MongoDB Atlas, use the full URI with credentials.

4. **Run the Application**
   ```
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   - UI: `http://localhost:8000/` (filters, pagination, upload, categories)
   - API: `http://localhost:8000/api/...`
   - Interactive docs: `http://localhost:8000/docs`

5. **Initialize Database**
   - The app automatically creates indexes on startup.

## ETL Pipeline (Data Import)

### Using ETL Script Directly
- Place your Excel/CSV files in a folder (e.g., `data/`).
- Run the import:
  ```python
  import asyncio
  from etl import import_folder

  async def main():
      results = await import_folder("path/to/your/data/folder")
      print(results)

  asyncio.run(main())
  ```

### Via API
- **Upload Single File**: `POST /api/profiles/import` (multipart form with file)
- **Import Folder**: `POST /api/profiles/import-folder?folder_path=/path/to/folder`

### Data Mapping
- The ETL assumes columns like: `Name`, `Current Role`, `Current Company`, `Location`, `Skills`, `Profile URL`.
- Skills should be comma/semicolon separated.
- Customize `MAPPING_TEMPLATE` in `etl.py` for your column names.
- Data is cleaned: trimmed, normalized companies, parsed skills, deduplicated by `profile_url`.

### Logging
- ETL logs inserted/updated/skipped counts to console.

## API Endpoints

All endpoints under `/api`.

### Profiles
- **GET /profiles** - List profiles (query params: `skip`, `limit`)
  - Response: `[{"id": "...", "name": "...", ...}]`
- **GET /profiles/{profile_id}** - Get single profile
  - Response: `{"id": "...", "name": "...", ...}`
- **PUT /profiles/{profile_id}** - Update profile (JSON body with optional fields)
  - Response: Updated profile
- **DELETE /profiles/{profile_id}** - Delete profile
  - Response: `{"message": "Profile deleted"}`

### Search
- **GET /profiles/search** - Filter profiles (query params: `role`, `location`, `skill`, `skip`, `limit`)
  - Examples:
    - Engineering Managers in Bangalore: `?role=Engineering Manager&location=Bangalore`
    - Profiles with Python skill: `?skill=Python`
  - Uses regex for role/location (case-insensitive), exact match for skills.
  - Response: List of matching profiles

### Import
- **POST /profiles/import** - Upload CSV/Excel file
  - Response: `{"message": "Import completed", "stats": {"inserted": 2, "updated": 0, "skipped": 0}}`
- **POST /profiles/import-folder** - Import from folder path (body: `{"folder_path": "/path"}`)

## MongoDB Schema

Each profile is a document:
```json
{
  "_id": "ObjectId(...)",
  "profile_id": "johndoe",
  "name": "John Doe",
  "current_role": "Engineering Manager",
  "current_company": "TechCorp",
  "location": "Bangalore",
  "skills": ["Python", "Java", "Leadership"],
  "experience": [{"company": "...", "role": "...", "start_date": "...", "end_date": "..."}],
  "education": [{"degree": "...", "institute": "...", "year": 2020}],
  "profile_url": "https://www.linkedin.com/in/johndoe",
  "last_scraped_at": "2023-10-01T00:00:00Z",
  "raw_json": {"Name": "John Doe", ...}
}
```

### Indexes
- Unique on `profile_url`
- On `current_role`, `skills`, `location` for efficient queries.

## Web UI Usage

1. Open `http://localhost:8000/`.
2. Use filters (Role, Location, Skill, Category) and pagination to browse profiles.
3. Upload CSV/Excel from the top-right uploader. Optionally provide a Category.
4. Switch to Categories view from the navbar to see grouped counts and quickly filter by a category.

## Example Usage

1. **Import Sample Data**
   - Use `example.csv` or upload via API.
   - After import, 3 profiles will be inserted.

2. **Sample Queries**
   - All profiles: `GET /api/profiles`
   - Engineering Managers in Bangalore: `GET /api/profiles/search?role=Engineering Manager&location=Bangalore`
     - Response: John Doe's profile
   - Profiles with Python: `GET /api/profiles/search?skill=Python`
     - Response: John Doe's profile

3. **Update Profile**
   ```bash
   curl -X PUT "http://localhost:8000/api/profiles/{id}" \
   -H "Content-Type: application/json" \
   -d '{"location": "New York"}'
   ```

4. **Demo Response Example**
   ```json
   {
     "id": "653f...abc",
     "name": "John Doe",
     "current_role": "Engineering Manager",
     "current_company": "TechCorp",
     "location": "Bangalore",
     "skills": ["Python", "Java", "Leadership"],
     "profile_url": "https://www.linkedin.com/in/johndoe",
     "last_scraped_at": "2023-10-01T12:00:00Z",
     "raw_json": {"Name": "John Doe", "Current Role": "Engineering Manager", ...}
   }
   ```

## Testing

1. Start MongoDB (local or Atlas).
2. Run the app.
3. Import `example.csv` via API or script.
4. Test endpoints using curl or Swagger docs.
5. Verify data in MongoDB (e.g., via MongoDB Compass).

## Notes
- Experience and Education fields are placeholders; extend `clean_profile_data` in `utils.py` to parse them from raw data.
- For production, add authentication, error handling, and async improvements.
- Deduplication based on `profile_url`; update logic if needed.

## Troubleshooting
- MongoDB connection issues: Check `.env` URI.
- Import errors: Ensure pandas can read your files; check column mappings.
- API errors: Use `/docs` for testing.
# linkdin-data-manager-with-UI
