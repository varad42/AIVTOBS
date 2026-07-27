import json
import os
import shutil
import tempfile
from io import BytesIO
from urllib.parse import urlparse

import requests

try:
    from google.cloud import storage
except ImportError:  # Optional legacy support for old GCS paths
    storage = None

from config import (
    GCS_BUCKET_NAME,
    GCS_JOBS_PREFIX,
    GCS_OUTPUT_PREFIX,
    GCS_UPLOAD_PREFIX,
    JOBS_FOLDER,
    OUTPUT_FOLDER,
    SUPABASE_ANON_KEY,
    SUPABASE_URL,
    UPLOAD_FOLDER,
)


_storage_client = None

SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "")
SUPABASE_STORAGE_ACCESS_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    SUPABASE_ANON_KEY,
)
SUPABASE_STORAGE_BASE_URL = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object" if SUPABASE_URL else ""


def use_supabase_storage():

    return bool(SUPABASE_URL and SUPABASE_STORAGE_BUCKET)


def use_cloud_storage():

    return bool(GCS_BUCKET_NAME or use_supabase_storage())


def get_storage_client():

    global _storage_client

    if storage is None:
        raise RuntimeError("google-cloud-storage is not installed, but a GCS path was requested.")

    if _storage_client is None:
        _storage_client = storage.Client()

    return _storage_client


def _strip_slashes(value):

    return str(value).strip().strip("/")


def _join_object_name(prefix, filename):

    cleaned_parts = [
        _strip_slashes(prefix),
        _strip_slashes(filename),
    ]
    return "/".join(part for part in cleaned_parts if part)


def build_upload_path(filename):

    if use_supabase_storage():
        return f"supabase://{SUPABASE_STORAGE_BUCKET}/{_join_object_name(GCS_UPLOAD_PREFIX, filename)}"

    if GCS_BUCKET_NAME:
        return f"gs://{GCS_BUCKET_NAME}/{_join_object_name(GCS_UPLOAD_PREFIX, filename)}"

    return os.path.join(UPLOAD_FOLDER, filename)


def build_job_path(filename):

    if use_supabase_storage():
        return f"supabase://{SUPABASE_STORAGE_BUCKET}/{_join_object_name(GCS_JOBS_PREFIX, filename)}"

    if GCS_BUCKET_NAME:
        return f"gs://{GCS_BUCKET_NAME}/{_join_object_name(GCS_JOBS_PREFIX, filename)}"

    return os.path.join(JOBS_FOLDER, filename)


def build_output_path(filename):

    if use_supabase_storage():
        return f"supabase://{SUPABASE_STORAGE_BUCKET}/{_join_object_name(GCS_OUTPUT_PREFIX, filename)}"

    if GCS_BUCKET_NAME:
        return f"gs://{GCS_BUCKET_NAME}/{_join_object_name(GCS_OUTPUT_PREFIX, filename)}"

    return os.path.join(OUTPUT_FOLDER, filename)


def is_cloud_path(path):

    return isinstance(path, str) and (
        path.startswith("gs://") or path.startswith("supabase://")
    )


def is_supabase_path(path):

    return isinstance(path, str) and path.startswith("supabase://")


def parse_cloud_path(path):

    parsed = urlparse(path)
    return parsed.netloc, parsed.path.lstrip("/")


def _get_supabase_object_url(path):

    bucket_name, object_name = parse_cloud_path(path)
    return f"{SUPABASE_STORAGE_BASE_URL}/{bucket_name}/{object_name}"


def _supabase_headers(content_type=None, extra_headers=None):

    headers = {
        "apikey": SUPABASE_STORAGE_ACCESS_KEY,
        "Authorization": f"Bearer {SUPABASE_STORAGE_ACCESS_KEY}",
    }

    if content_type:
        headers["Content-Type"] = content_type

    if extra_headers:
        headers.update(extra_headers)

    return headers


def _supabase_request(method, path, data=None, content_type=None, extra_headers=None, params=None):

    if not SUPABASE_STORAGE_BASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured.")

    if not SUPABASE_STORAGE_ACCESS_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY is not configured.")

    response = requests.request(
        method,
        _get_supabase_object_url(path),
        headers=_supabase_headers(content_type=content_type, extra_headers=extra_headers),
        params=params,
        data=data,
        timeout=60,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase storage request failed for {path}: "
            f"{response.status_code} {response.text}"
        )

    return response


def get_blob(path):

    bucket_name, blob_name = parse_cloud_path(path)
    bucket = get_storage_client().bucket(bucket_name)
    return bucket.blob(blob_name)


def exists(path):

    if not path:
        return False

    if is_supabase_path(path):
        response = requests.get(
            _get_supabase_object_url(path),
            headers=_supabase_headers(),
            timeout=30,
        )
        if response.status_code == 404:
            return False
        if response.status_code >= 400:
            raise RuntimeError(
                f"Supabase storage existence check failed for {path}: "
                f"{response.status_code} {response.text}"
            )
        return True

    if is_cloud_path(path):
        return get_blob(path).exists()

    return os.path.exists(path)


def save_upload(file_storage, destination_path):

    if is_supabase_path(destination_path):
        content_type = getattr(file_storage, "mimetype", None) or "application/octet-stream"
        file_storage.stream.seek(0)
        _supabase_request(
            "POST",
            destination_path,
            data=file_storage.stream.read(),
            content_type=content_type,
            extra_headers={"x-upsert": "true"},
        )
        return

    if is_cloud_path(destination_path):
        blob = get_blob(destination_path)
        content_type = getattr(file_storage, "mimetype", None)
        blob.upload_from_file(file_storage.stream, content_type=content_type, rewind=True)
        return

    file_storage.save(destination_path)


def upload_text(path, text, content_type="text/plain; charset=utf-8"):

    if is_supabase_path(path):
        _supabase_request(
            "POST",
            path,
            data=text.encode("utf-8"),
            content_type=content_type,
            extra_headers={"x-upsert": "true"},
        )
        return

    if is_cloud_path(path):
        get_blob(path).upload_from_string(text, content_type=content_type)
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file_handle:
        file_handle.write(text)


def read_text(path):

    if is_supabase_path(path):
        response = _supabase_request("GET", path)
        return response.text

    if is_cloud_path(path):
        return get_blob(path).download_as_text(encoding="utf-8")

    with open(path, "r", encoding="utf-8") as file_handle:
        return file_handle.read()


def upload_json(path, data):

    upload_text(
        path,
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json"
    )


def read_json(path):

    return json.loads(read_text(path))


def upload_local_file(local_path, destination_path, content_type=None):

    if is_supabase_path(destination_path):
        with open(local_path, "rb") as file_handle:
            _supabase_request(
                "POST",
                destination_path,
                data=file_handle.read(),
                content_type=content_type or "application/octet-stream",
                extra_headers={"x-upsert": "true"},
            )
        return

    if is_cloud_path(destination_path):
        get_blob(destination_path).upload_from_filename(local_path, content_type=content_type)
        return

    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    shutil.copyfile(local_path, destination_path)


def download_to_local(source_path, suffix="", temp_dir=None):

    if not source_path:
        raise RuntimeError("A source path is required for download.")

    if not is_cloud_path(source_path):
        return source_path

    file_handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=temp_dir)
    file_handle.close()

    if is_supabase_path(source_path):
        response = _supabase_request("GET", source_path)
        with open(file_handle.name, "wb") as output_handle:
            output_handle.write(response.content)
        return file_handle.name

    get_blob(source_path).download_to_filename(file_handle.name)
    return file_handle.name


def download_bytes(path):

    if is_supabase_path(path):
        response = _supabase_request("GET", path)
        return response.content

    if is_cloud_path(path):
        return get_blob(path).download_as_bytes()

    with open(path, "rb") as file_handle:
        return file_handle.read()


def open_bytes_io(path):

    return BytesIO(download_bytes(path))
