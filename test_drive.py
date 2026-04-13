import os
import sys

# Ensure project root is on the path so bot/ and config/ are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.services.drive_service import get_all_documents_text

if __name__ == "__main__":
    print("Fetching documents from Google Drive...\n")

    text, image_ids = get_all_documents_text()

    if not text and not image_ids:
        print("No content retrieved. Check your credentials.json and GOOGLE_DRIVE_FOLDER_ID.")
    else:
        print(f"Total characters retrieved: {len(text)}")
        print(f"Image files found: {len(image_ids)}")
        if image_ids:
            print(f"Image file IDs: {image_ids}")
        print("\n--- First 500 characters ---")
        print(text[:500])
