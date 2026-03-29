import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from pymongo import MongoClient


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

OLD_MONGO_URI = os.getenv("OLD_MONGO_URI") or os.getenv("MONGO_URI", "")
OLD_MONGO_DB_NAME = os.getenv("OLD_MONGO_DB_NAME", "ai_video_blog")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY", "")


def require_env(name, value):

    if not value:
        raise RuntimeError(f"{name} is not configured.")


def serialize_value(value):

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            pass

    if isinstance(value, dict):
        return {
            key: serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            serialize_value(item)
            for item in value
        ]

    return value


def supabase_headers():

    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def insert_document(table_name, document):

    response = requests.post(
        f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}",
        headers=supabase_headers(),
        params={"select": "id"},
        json={"data": document},
        timeout=30
    )
    response.raise_for_status()
    rows = response.json()
    return rows[0]["id"] if rows else None


def migrate_collection(mongo_db, collection_name):

    collection = mongo_db[collection_name]
    inserted_count = 0

    for document in collection.find():
        document.pop("_id", None)
        serialized_document = serialize_value(document)
        insert_document(collection_name, serialized_document)
        inserted_count += 1

    return inserted_count


def main():

    require_env("OLD_MONGO_URI", OLD_MONGO_URI)
    require_env("SUPABASE_URL", SUPABASE_URL)
    require_env("SUPABASE_ANON_KEY", SUPABASE_ANON_KEY)

    mongo_client = MongoClient(OLD_MONGO_URI)
    mongo_db = mongo_client[OLD_MONGO_DB_NAME]

    for collection_name in ("users", "jobs", "blogs"):
        count = migrate_collection(mongo_db, collection_name)
        print(f"Migrated {count} documents into {collection_name}")

    print("Mongo to Supabase migration complete.")


if __name__ == "__main__":
    main()
