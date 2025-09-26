# TODO: Fix Profile Import for Role/Title Distinction

## Overall Goal
Auto-tag profiles with category from CSV filename during import, so profiles from different role CSVs (e.g., senior_software_engineer) are distinguishable via filters/searches. Ensure each profile remains a separate DB document.

## Steps
- [x] Step 1: Edit etl.py to auto-detect and set category from CSV filename (using regex on patterns like "linkedin_{role}_results.csv") if no CLI category provided. Update import_csv_file to log the category used.
- [x] Step 2: Edit run_import.py to print detected/applied categories in the summary output for user feedback.
- [x] Step 3: (Optional) Add a new endpoint in routes.py for grouping profiles by category (e.g., /profiles/by-category) to make UI integration easier.
- [x] Step 4: Test the changes – Run import without CLI category on sample CSVs, verify in DB via API or mongosh that profiles have correct categories and are separate.
- [x] Step 5: Update this TODO.md with completion notes and close the task.

Progress: All steps completed.

## Completion Notes
- Import test: Ran `python run_import.py` – successfully auto-detected "Senior Software Engineer" from filename, updated 120 profiles with the category. No new inserts (existing data), but confirms tagging works.
- Verification: Each profile is stored as a separate MongoDB document (per original logic). Categories enable distinction via API filters (e.g., /api/profiles/search?category=Senior%20Software%20Engineer) or the new /api/profiles/by-category endpoint, which groups by category with counts and sample profiles.
- UI Integration: Your frontend (screenshot) can now use the search params or by-category endpoint for role-based views/filters, preventing mix-up.
- Task Closed: Profiles will now be tagged by role/title from CSV names, making them easily distinguishable without manual CLI input.

# TODO: Add Connection/Profile Selection for Imports

## Overall Goal
Modify the import process to prompt the user for a "connection" or "profile" name at runtime (e.g., "hrbp" or "engineering_manager"). Save imported data to a dynamic MongoDB collection named "profiles_{connection_name}" (e.g., "profiles_hrbp"). This allows separate collections for different connections without mixing data. Retain existing category tagging.

## Steps
- [ ] Step 1: Update db.py to make get_collection accept an optional connection_name parameter. If provided, return database[f"profiles_{connection_name.lower()}"] (sanitize to lowercase). Auto-call create_indexes on the dynamic collection if needed.
- [ ] Step 2: Update etl.py – Modify import_folder and import_csv_file to accept and forward connection_name to get_collection(connection_name). No changes to data processing logic.
- [ ] Step 3: Update run_import.py – In main(), add input prompt for connection_name (e.g., "Enter connection name: "). Pass it to import_folder along with category. Display the used connection in logs/summary.
- [ ] Step 4: Test the changes – Place a sample CSV in data_to_import/, run `python run_import.py`, input a connection name, verify in MongoDB (via Compass or mongosh) that a new collection is created, indexes are set, and data is inserted there. Run again with different name to confirm separation.
- [ ] Step 5: (Optional) Update README.md to explain the new prompting feature and dynamic collections.
- [ ] Step 6: Update this TODO.md with completion notes and mark as done.
