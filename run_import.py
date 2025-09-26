import asyncio
from etl import import_folder
import os
import sys

# --- INSTRUCTIONS ---
# 1. Create a folder named 'data_to_import' in your project directory.
# 2. Download your Google Sheets as CSV files and place them in the 'data_to_import' folder.
# 3. Make sure your MongoDB server is running and you have created a .env file with the MONGODB_URI.
# 4. Run this script from your terminal: python run_import.py [category]
#    (Replace [category] with the desired category name, e.g., python run_import.py hrbp)
# --------------------

async def main(category=None):
    """The main function to run the import process."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    import_folder_path = os.path.join(project_root, 'data_to_import')

    if not os.path.exists(import_folder_path) or not os.listdir(import_folder_path):
        print(f"Error: The folder '{import_folder_path}' is either missing or empty.")
        print("Please create it and add your CSV files.")
        return

    print(f"Starting import from folder: {import_folder_path}")
    if category:
        print(f"Using category: {category}")
    try:
        results = await import_folder(import_folder_path, category)
        print("\nImport process finished.")
        print("Summary:")
        if not results:
            print("  No files were processed. Make sure your files have a .csv, .xlsx, or .xls extension.")
        for file_name, result in results.items():
            cat = result.get('category', 'None (CLI-provided or not set)')
            print(f"  - {file_name} (Category: {cat}): Inserted {result.get('inserted', 0)}, Updated {result.get('updated', 0)}")
    except Exception as e:
        print(f"An error occurred during the import process: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("MONGODB_URI"):
        print("Error: MONGODB_URI is not set in your .env file.")
        print("Please create a .env file with: MONGODB_URI='your_mongodb_connection_string'")
    else:
        category = sys.argv[1] if len(sys.argv) > 1 else None
        print("MongoDB URI found. Running importer...")
        asyncio.run(main(category))
