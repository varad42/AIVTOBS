import copy
from dataclasses import dataclass
from datetime import date, datetime

import requests

from config import SUPABASE_ANON_KEY, SUPABASE_URL


def _serialize_value(value):

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: _serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _serialize_value(item)
            for item in value
        ]

    return value


def _parse_datetime_if_possible(value):

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        return value

    normalized_value = value.replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(normalized_value)
    except ValueError:
        return value


def _compare_values(left, right):

    parsed_left = _parse_datetime_if_possible(left)
    parsed_right = _parse_datetime_if_possible(right)

    if (
        isinstance(parsed_left, datetime)
        and isinstance(parsed_right, datetime)
    ):
        return parsed_left, parsed_right

    return left, right


def _matches_condition(document_value, condition):

    for operator, expected_value in condition.items():
        comparable_document_value, comparable_expected_value = _compare_values(
            document_value,
            expected_value
        )

        if operator == "$in":
            if comparable_document_value not in expected_value:
                return False
            continue

        if operator == "$gt":
            if comparable_document_value is None or comparable_document_value <= comparable_expected_value:
                return False
            continue

        if operator == "$gte":
            if comparable_document_value is None or comparable_document_value < comparable_expected_value:
                return False
            continue

        raise ValueError(f"Unsupported query operator: {operator}")

    return True


def _matches_filter(document, filter_spec):

    if not filter_spec:
        return True

    for field_name, expected_value in filter_spec.items():
        document_value = document.get(field_name)

        if isinstance(expected_value, dict):
            if not _matches_condition(document_value, expected_value):
                return False
            continue

        if document_value != expected_value:
            return False

    return True


def _sort_documents(documents, sort_spec):

    if not sort_spec:
        return documents

    sorted_documents = list(documents)

    for field_name, direction in reversed(sort_spec):
        reverse = direction == -1
        sorted_documents.sort(
            key=lambda document: document.get(field_name),
            reverse=reverse
        )

    return sorted_documents


def _row_to_document(row):

    document = copy.deepcopy(row.get("data") or {})
    document["_id"] = row["id"]
    return document


def _apply_update(document, update_spec):

    updated_document = copy.deepcopy(document)

    for field_name, field_value in update_spec.get("$set", {}).items():
        updated_document[field_name] = field_value

    for field_name in update_spec.get("$unset", {}).keys():
        updated_document.pop(field_name, None)

    return updated_document


@dataclass
class InsertOneResult:
    inserted_id: int


@dataclass
class UpdateResult:
    matched_count: int
    modified_count: int
    upserted_id: int | None = None


class CollectionCursor:

    def __init__(self, documents):
        self._documents = list(documents)

    def sort(self, field_name, direction):
        self._documents = _sort_documents(
            self._documents,
            [(field_name, direction)]
        )
        return self

    def limit(self, count):
        self._documents = self._documents[:count]
        return self

    def __iter__(self):
        return iter(self._documents)

    def __len__(self):
        return len(self._documents)


class SupabaseCollection:

    def __init__(self, table_name):
        self.table_name = table_name

    def _base_url(self):

        if not SUPABASE_URL:
            raise RuntimeError("SUPABASE_URL is not configured.")

        if not SUPABASE_ANON_KEY:
            raise RuntimeError("SUPABASE_ANON_KEY is not configured.")

        return f"{SUPABASE_URL.rstrip('/')}/rest/v1/{self.table_name}"

    def _headers(self, prefer=None):

        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
        }

        if prefer:
            headers["Prefer"] = prefer

        return headers

    def _request(self, method, params=None, json_payload=None, prefer=None):

        response = requests.request(
            method,
            self._base_url(),
            headers=self._headers(prefer=prefer),
            params=params,
            json=json_payload,
            timeout=20
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Supabase request failed for table {self.table_name}: "
                f"{response.status_code} {response.text}"
            )

        if not response.text.strip():
            return None

        return response.json()

    def _fetch_first_by_status(self, status):

        rows = self._request(
            "GET",
            params={
                "select": "id,data,created_at,updated_at",
                "data->>status": f"eq.{status}",
                "order": "id.asc",
                "limit": "1"
            }
        )

        if not rows:
            return None

        return _row_to_document(rows[0])

    def _list_rows(self):

        rows = self._request(
            "GET",
            params={
                "select": "id,data,created_at,updated_at",
                "order": "id.asc"
            }
        )

        return rows or []

    def _documents(self):

        return [
            _row_to_document(row)
            for row in self._list_rows()
        ]

    def find(self, filter_spec=None):

        matching_documents = [
            document
            for document in self._documents()
            if _matches_filter(document, filter_spec)
        ]

        return CollectionCursor(matching_documents)

    def find_one(self, filter_spec=None, sort=None):

        documents = self.find(filter_spec)

        if sort:
            documents = CollectionCursor(
                _sort_documents(list(documents), sort)
            )

        for document in documents:
            return document

        return None

    def insert_one(self, document):

        serialized_document = _serialize_value(document)
        rows = self._request(
            "POST",
            params={"select": "id,data,created_at,updated_at"},
            json_payload={"data": serialized_document},
            prefer="return=representation"
        )

        inserted_row = (rows or [None])[0]

        if not inserted_row:
            raise RuntimeError(f"Supabase insert did not return a row for table {self.table_name}.")

        return InsertOneResult(inserted_id=inserted_row["id"])

    def update_one(self, filter_spec, update_spec, upsert=False):

        existing_document = self.find_one(filter_spec)

        if not existing_document:
            if not upsert:
                return UpdateResult(matched_count=0, modified_count=0)

            new_document = {}

            for field_name, field_value in (filter_spec or {}).items():
                if not isinstance(field_value, dict):
                    new_document[field_name] = field_value

            new_document = _apply_update(new_document, update_spec)
            insert_result = self.insert_one(new_document)
            return UpdateResult(
                matched_count=0,
                modified_count=0,
                upserted_id=insert_result.inserted_id
            )

        updated_document = _apply_update(existing_document, update_spec)
        document_id = existing_document["_id"]
        serialized_document = _serialize_value(
            {
                key: value
                for key, value in updated_document.items()
                if key != "_id"
            }
        )

        rows = self._request(
            "PATCH",
            params={
                "id": f"eq.{document_id}",
                "select": "id,data,created_at,updated_at"
            },
            json_payload={"data": serialized_document},
            prefer="return=representation"
        )

        if not rows:
            return UpdateResult(matched_count=0, modified_count=0)

        return UpdateResult(matched_count=1, modified_count=1)

    def find_one_and_update(self, filter_spec, update_spec, return_document=None):
        existing_document = self.find_one(filter_spec)

        if not existing_document:
            return None

        self.update_one({"_id": existing_document["_id"]}, update_spec)
        return self.find_one({"_id": existing_document["_id"]})


users_collection = SupabaseCollection("users")
jobs_collection = SupabaseCollection("jobs")
blogs_collection = SupabaseCollection("blogs")

print("Supabase REST connected")
