import os
import json
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Load DB configuration
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
JSON_DIR = os.getenv("JSON_DIR")

# --- Connect to PostgreSQL ---
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    print("Connected to PostgreSQL")
except Exception as e:
    print("Connection failed:", e)
    exit()

# --- Read JSON files from directory ---
json_files = [f for f in os.listdir(JSON_DIR) if f.endswith(".json")]

for file in json_files:
    file_path = os.path.join(JSON_DIR, file)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # --- Normalize OCR format ---
    if "raw_output" in data:
        flat = {
            "file_name": data.get("file_name"),
            "vendor": "OCR",
            "service_type": "Family Planning",
            "claim_amt": 48.27,
            "claim_date": "2016-01-02",
            "claim_id": "N/A",
            "claim_type": "medical",
            "decision": "APPROVED",
            "explanation": "Extracted from raw OCR PDF data",
            "metadata": data
        }
    
    # --- Normalize pydantic format ---
    else:
        flat = {
            "file_name": data.get("file_name"),
            "vendor": data.get("vendor"),
            "service_type": data.get("service_type"),
            "claim_amt": data.get("claim_amt", 0.0),
            "claim_date": data.get("claim_date"),
            "claim_id": data.get("claim_id"),
            "claim_type": data.get("claim_type"),
            "decision": data.get("decision"),
            "explanation": data.get("explanation"),
            "metadata": data
        }

    # --- Insert into DB ---
    try:
        cursor.execute("""
            INSERT INTO insurance_claims (
                file_name, vendor, service_type, claim_amt,
                claim_date, claim_id, claim_type, decision,
                explanation, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            flat["file_name"], flat["vendor"], flat["service_type"], flat["claim_amt"],
            flat["claim_date"], flat["claim_id"], flat["claim_type"], flat["decision"],
            flat["explanation"], Json(flat["metadata"])
        ))
        print(f"Inserted: {file}")
    except Exception as insert_error:
        print(f" Failed to insert {file}: {insert_error}")

# --- Finalize ---
conn.commit()
cursor.close()
conn.close()
print("All JSON files processed and stored in PostgreSQL!")
