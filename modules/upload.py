from flask import Blueprint, jsonify, redirect, request, send_file, session, flash
import os
import re
import requests
import subprocess
import time
import uuid
from io import BytesIO
from urllib.parse import parse_qs, unquote, urlparse
from datetime import datetime, timedelta, timezone

from database.mongo import jobs_collection
from modules.cloud_storage import build_upload_path, save_upload

upload_bp = Blueprint("upload", __name__)
DEDUPLICATION_WINDOW_MINUTES = 1
ACTIVE_JOB_STATUSES = [
    "uploading",
    "uploaded",
    "processing",
    "downloading",
    "extracting_audio",
    "transcribing",
    "waiting_for_model",
    "summarize_requested",
    "blog_requested",
]


def slugify(value):

    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")

    return value or "video"


def build_job_slug(video_filename, youtube_url, job_id):

    if video_filename:
        source_name = os.path.splitext(video_filename)[0]
    elif youtube_url:
        source_name = urlparse(youtube_url).netloc.replace("www.", "")
    else:
        source_name = "video"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_id = job_id.split("-")[0]

    return f"{slugify(source_name)}_{timestamp}_{short_id}"


def prettify_title(value):

    cleaned_value = re.sub(r"[_\-]+", " ", value or "")
    cleaned_value = re.sub(r"\s+", " ", cleaned_value).strip()
    return cleaned_value or "Video"


def get_video_title_from_url(video_url):

    if not video_url:
        return ""

    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "%(title)s", "--skip-download", video_url],
            capture_output=True,
            text=True,
            check=True,
            timeout=20
        )
        title = (result.stdout or "").strip().splitlines()
        if title:
            return title[-1].strip()
    except Exception:
        pass

    parsed_url = urlparse(video_url)
    path_name = os.path.basename(unquote(parsed_url.path.rstrip("/")))
    if path_name:
        return prettify_title(os.path.splitext(path_name)[0])

    return prettify_title(parsed_url.netloc.replace("www.", ""))


def is_youtube_url(url):

    hostname = urlparse(url).netloc.lower()
    return "youtube.com" in hostname or "youtu.be" in hostname


def extract_youtube_video_id(url):

    parsed_url = urlparse(url)
    hostname = parsed_url.netloc.lower()

    if "youtu.be" in hostname:
        return parsed_url.path.lstrip("/").split("/")[0]

    if "youtube.com" in hostname:
        query_video_id = parse_qs(parsed_url.query).get("v", [])
        if query_video_id:
            return query_video_id[0]

        path_parts = [part for part in parsed_url.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts", "live"}:
            return path_parts[1]

    return ""


def build_source_identifier(video, video_url):

    if video and video.filename:
        return os.path.basename(video.filename).strip().lower()

    return (video_url or "").strip()


def find_recent_duplicate_job(user, source_type, source_identifier):

    if not source_identifier:
        return None

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=DEDUPLICATION_WINDOW_MINUTES)

    return jobs_collection.find_one(
        {
            "user": user,
            "source_type": source_type,
            "file": source_identifier,
            "status": {
                "$in": [
                    "uploaded",
                    "processing",
                    "downloading",
                    "extracting_audio",
                    "transcribing",
                    "waiting_for_model",
                    "summarize_requested",
                    "summary_ready",
                    "blog_ready"
                ]
            },
            "uploaded_at": {"$gte": cutoff},
            "source_identifier": source_identifier
        },
        sort=[("_id", -1)]
    )


def supersede_active_jobs(user, source_type, source_identifier, new_job_id):

    if not source_identifier:
        return

    matching_jobs = jobs_collection.find(
        {
            "user": user,
            "source_type": source_type,
            "source_identifier": source_identifier,
            "status": {"$in": ACTIVE_JOB_STATUSES},
        }
    )

    for job in matching_jobs:
        if job.get("job_id") == new_job_id:
            continue

        jobs_collection.update_one(
            {"job_id": job["job_id"]},
            {
                "$set": {
                    "status": "superseded",
                    "superseded_at": datetime.now(timezone.utc),
                    "superseded_by": new_job_id,
                    "error_message": "A newer upload of the same video was started."
                }
            }
        )


@upload_bp.route("/youtube_preview")
def youtube_preview():

    video_url = (request.args.get("url") or "").strip()

    if not video_url or not is_youtube_url(video_url):
        return jsonify({"error": "A valid YouTube URL is required."}), 400

    video_id = extract_youtube_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Could not determine the YouTube video id."}), 400

    title = get_video_title_from_url(video_url) or "YouTube video"

    return jsonify(
        {
            "title": title,
            "thumbnail_url": f"/youtube_thumbnail/{video_id}"
        }
    )


@upload_bp.route("/youtube_thumbnail/<video_id>")
def youtube_thumbnail(video_id):

    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    response = requests.get(thumbnail_url, timeout=15)
    response.raise_for_status()

    return send_file(
        BytesIO(response.content),
        mimetype=response.headers.get("Content-Type", "image/jpeg")
    )


@upload_bp.route("/upload", methods=["GET", "POST"])
def upload():

    print("Upload route called")

    if "user" not in session:
        print("Upload blocked: no active session")
        return redirect("/")

    if request.method == "GET":
        return redirect("/dashboard")

    if request.method == "POST":

        video = request.files.get("video")
        youtube_url = (request.form.get("video_url") or request.form.get("youtube") or "").strip()
        job_id = str(uuid.uuid4())
        display_name = (
            prettify_title(os.path.splitext(video.filename)[0])
            if video and video.filename
            else get_video_title_from_url(youtube_url)
        )
        job_slug = build_job_slug(
            video.filename if video else "",
            youtube_url,
            job_id
        )

        file_path = ""
        source_type = "youtube"
        local_upload_seconds = None
        source_identifier = build_source_identifier(video, youtube_url)

        if video and video.filename != "":
            print(f"Video file received: {video.filename}")
            source_type = "local"

            file_extension = os.path.splitext(video.filename)[1]
            file_path = build_upload_path(f"{job_slug}{file_extension}")

            placeholder_job = {
                "job_id": job_id,
                "job_slug": job_slug,
                "display_name": display_name,
                "user": session["user"],
                "file": file_path,
                "source_type": source_type,
                "source_identifier": source_identifier,
                "status": "uploading",
                "queued_at": datetime.now(timezone.utc),
                "local_upload_seconds": None,
                "transcription_provider": "whisper",
                "summary_model": None,
                "blog": None
            }
            jobs_collection.insert_one(placeholder_job)
            supersede_active_jobs(
                session["user"],
                source_type,
                source_identifier,
                job_id
            )
            print(f"Job placeholder created before upload: {job_id} ({job_slug})")

            local_upload_started_at = time.perf_counter()
            save_upload(video, file_path)
            local_upload_seconds = time.perf_counter() - local_upload_started_at
            print(f"Video saved to: {file_path}")

            jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": "uploaded",
                        "uploaded_at": datetime.now(timezone.utc),
                        "local_upload_seconds": local_upload_seconds
                    }
                }
            )
            print(f"Local upload completed and queued: {job_id}")

        elif youtube_url:
            source_type = "youtube" if is_youtube_url(youtube_url) else "external_url"
            print(f"Video URL received: {youtube_url} ({source_type})")

            file_path = youtube_url

        else:
            print("Upload failed: no video file or video URL provided")
            flash("Add a video file or video URL before starting processing.", "error")
            return redirect("/dashboard")

        job_data = {

            "job_id": job_id,
            "job_slug": job_slug,
            "display_name": display_name,
            "user": session["user"],
            "file": file_path,
            "source_type": source_type,
            "source_identifier": source_identifier,
            "status": "uploaded",
            "uploaded_at": datetime.now(timezone.utc),
            "queued_at": datetime.now(timezone.utc),
            "local_upload_seconds": local_upload_seconds,
            "transcription_provider": "whisper",
            "summary_model": None,
            "blog": None

        }

        if source_type != "local":
            jobs_collection.insert_one(job_data)
            supersede_active_jobs(
                session["user"],
                source_type,
                source_identifier,
                job_id
            )
            print(f"Job created: {job_id} ({job_slug})")

        return redirect(f"/dashboard?job_id={job_id}")
    return redirect("/dashboard")
