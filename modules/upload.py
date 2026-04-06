from flask import Blueprint, render_template, request, redirect, session, flash
import os
import re
import subprocess
import time
import uuid
from urllib.parse import unquote, urlparse
from datetime import datetime, timedelta, timezone

from database.mongo import jobs_collection
from modules.cloud_storage import build_upload_path, save_upload

upload_bp = Blueprint("upload", __name__)
DEDUPLICATION_WINDOW_MINUTES = 1


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
            "uploaded_at": {"$gte": cutoff}
        },
        sort=[("_id", -1)]
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
        source_identifier = ""

        if video and video.filename != "":
            print(f"Video file received: {video.filename}")
            source_type = "local"

            file_extension = os.path.splitext(video.filename)[1]
            file_path = build_upload_path(f"{job_slug}{file_extension}")

            source_identifier = file_path
            duplicate_job = find_recent_duplicate_job(
                session["user"],
                source_type,
                source_identifier
            )

            if duplicate_job:
                print(f"Duplicate local upload detected, reusing job {duplicate_job['job_id']}")
                flash("A recent job for this file already exists. Reusing that job instead of starting a duplicate.", "info")
                return redirect(f"/dashboard?job_id={duplicate_job['job_id']}")

            placeholder_job = {
                "job_id": job_id,
                "job_slug": job_slug,
                "display_name": display_name,
                "user": session["user"],
                "file": file_path,
                "source_type": source_type,
                "status": "uploading",
                "queued_at": datetime.now(timezone.utc),
                "local_upload_seconds": None,
                "transcription_provider": "whisper",
                "summary_model": None,
                "blog": None
            }
            jobs_collection.insert_one(placeholder_job)
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
            source_identifier = file_path

            duplicate_job = find_recent_duplicate_job(
                session["user"],
                source_type,
                source_identifier
            )

            if duplicate_job:
                print(f"Duplicate URL job detected, reusing job {duplicate_job['job_id']}")
                flash("A recent job for this URL already exists. Reusing that job instead of starting a duplicate.", "info")
                return redirect(f"/dashboard?job_id={duplicate_job['job_id']}")

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
            print(f"Job created: {job_id} ({job_slug})")

        return redirect(f"/dashboard?job_id={job_id}")
    return redirect("/dashboard")
