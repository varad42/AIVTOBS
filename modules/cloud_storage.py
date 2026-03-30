import json
import os
import shutil
import tempfile
from io import BytesIO
from urllib.parse import urlparse

from google.cloud import storage

from config import (
    GCS_BUCKET_NAME,
    GCS_JOBS_PREFIX,
    GCS_OUTPUT_PREFIX,
    GCS_UPLOAD_PREFIX,
    JOBS_FOLDER,
    OUTPUT_FOLDER,
    UPLOAD_FOLDER,
)


_storage_client = None


def use_cloud_storage():

    return bool(GCS_BUCKET_NAME)


def get_storage_client():

    global _storage_client

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

    if use_cloud_storage():
        return f"gs://{GCS_BUCKET_NAME}/{_join_object_name(GCS_UPLOAD_PREFIX, filename)}"

    return os.path.join(UPLOAD_FOLDER, filename)


def build_job_path(filename):

    if use_cloud_storage():
        return f"gs://{GCS_BUCKET_NAME}/{_join_object_name(GCS_JOBS_PREFIX, filename)}"

    return os.path.join(JOBS_FOLDER, filename)


def build_output_path(filename):

    if use_cloud_storage():
        return f"gs://{GCS_BUCKET_NAME}/{_join_object_name(GCS_OUTPUT_PREFIX, filename)}"

    return os.path.join(OUTPUT_FOLDER, filename)


def is_cloud_path(path):

    return isinstance(path, str) and path.startswith("gs://")


def parse_cloud_path(path):

    parsed = urlparse(path)
    return parsed.netloc, parsed.path.lstrip("/")


def get_blob(path):

    bucket_name, blob_name = parse_cloud_path(path)
    bucket = get_storage_client().bucket(bucket_name)
    return bucket.blob(blob_name)


def exists(path):

    if not path:
        return False

    if is_cloud_path(path):
        return get_blob(path).exists()

    return os.path.exists(path)


def save_upload(file_storage, destination_path):

    if is_cloud_path(destination_path):
        blob = get_blob(destination_path)
        content_type = getattr(file_storage, "mimetype", None)
        blob.upload_from_file(file_storage.stream, content_type=content_type, rewind=True)
        return

    file_storage.save(destination_path)


def upload_text(path, text, content_type="text/plain; charset=utf-8"):

    if is_cloud_path(path):
        get_blob(path).upload_from_string(text, content_type=content_type)
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file_handle:
        file_handle.write(text)


def read_text(path):

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
    get_blob(source_path).download_to_filename(file_handle.name)
    return file_handle.name


def download_bytes(path):

    if is_cloud_path(path):
        return get_blob(path).download_as_bytes()

    with open(path, "rb") as file_handle:
        return file_handle.read()


def open_bytes_io(path):

    return BytesIO(download_bytes(path))
