import os
import logging
from typing import List, Dict, Any

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("paa_sheets")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheets_client():
    """Initialize and return a gspread client using env vars."""
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    client_email = os.getenv("GOOGLE_CLIENT_EMAIL")
    private_key = os.getenv("GOOGLE_PRIVATE_KEY")
    project_id = os.getenv("GOOGLE_PROJECT_ID")

    if not all([sheet_id, client_email, private_key]):
        logger.warning("Google Sheets credentials not fully configured in environment.")
        return None, None

    # Handle private key formatting (newlines might be literal '\\n' in env var)
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")
    # Remove quotes if they are surrounding the string
    if private_key.startswith('"') and private_key.endswith('"'):
        private_key = private_key[1:-1]

    credentials_dict = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": "",
        "private_key": private_key,
        "client_email": client_email,
        "client_id": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email.replace('@', '%40')}"
    }

    try:
        credentials = Credentials.from_service_account_info(
            credentials_dict, scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        return client, sheet_id
    except Exception as e:
        logger.error(f"Failed to authenticate with Google Sheets: {e}")
        return None, None

def get_existing_counts() -> Dict[str, int]:
    """Read the 'Headless' worksheet and return a mapping of {keyword: count}."""
    client, sheet_id = get_sheets_client()
    if not client or not sheet_id:
        return {}

    try:
        sheet = client.open_by_key(sheet_id).worksheet("Headless")
        records = sheet.get_all_records()
        
        counts = {}
        for row in records:
            keyword = str(row.get("Keyword", "")).strip()
            if keyword:
                counts[keyword] = counts.get(keyword, 0) + 1
        return counts
    except Exception as e:
        logger.error(f"Error reading existing counts from Google Sheets: {e}")
        return {}

def save_to_sheets(results: List[Dict[str, Any]], clear_first: bool = False):
    """Save scraped PAA results to Google Sheets. Each question on a new row."""
    client, sheet_id = get_sheets_client()
    if not client or not sheet_id:
        return {"status": "skipped", "message": "Google Sheets not configured or auth failed."}

    try:
        # Open the specific worksheet named "Headless"
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet("Headless")
        
        # Check if headers exist, if not create them
        try:
            headers = sheet.row_values(1)
            if not headers:
                sheet.append_row(["Keyword", "Region", "Question"])
        except Exception:
            sheet.append_row(["Keyword", "Region", "Question"])

        if clear_first:
            # If we want to replace, we'd need to find and delete rows. 
            # For simplicity in this n8n version, we'll just append.
            # But the user might prefer not having duplicates. 
            pass

        rows_to_add = []
        for result in results:
            keyword = result.get("keyword", "")
            region = result.get("region", "")
            questions = result.get("questions", [])
            
            for q in questions:
                rows_to_add.append([keyword, region, q])

        if rows_to_add:
            sheet.append_rows(rows_to_add)
            logger.info(f"Successfully appended {len(rows_to_add)} rows to Google Sheet.")
            return {"status": "success", "count": len(rows_to_add)}
        return {"status": "skipped", "message": "No questions to add."}

    except Exception as e:
        logger.error(f"Error saving to Google Sheets: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Test execution
    res = save_to_sheets([{"keyword": "test keyword", "region": "us", "questions": ["Test Question 1", "Test Question 2"]}])
    print(res)
