from flask import Blueprint, render_template, request, redirect, session, flash
import os
import re
import uuid
from urllib.parse import urlparse
from datetime import datetime, timezone

from config import DEEPGRAM_API_KEY, UPLOAD_FOLDER
from database.mongo import jobs_collection

upload_bp = Blueprint("upload", __name__)


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
        youtube_url = request.form.get("youtube")
        transcription_provider = request.form.get("transcription_provider", "whisper")
        deepgram_model = request.form.get("deepgram_model", "nova-3")

        if transcription_provider not in {"whisper", "deepgram"}:
            flash("Choose a valid transcription provider before continuing.", "error")
            return redirect("/dashboard")

        if deepgram_model not in {"base", "nova-3"}:
            flash("Choose a valid Deepgram model before continuing.", "error")
            return redirect("/dashboard")

        if transcription_provider == "deepgram" and not DEEPGRAM_API_KEY:
            flash("Deepgram is not configured yet. Add `DEEPGRAM_API_KEY` in your `.env` file to use it.", "error")
            return redirect("/dashboard")

        job_id = str(uuid.uuid4())
        job_slug = build_job_slug(
            video.filename if video else "",
            youtube_url,
            job_id
        )

        file_path = ""

        if video and video.filename != "":
            print(f"Video file received: {video.filename}")

            file_path = os.path.join(
                UPLOAD_FOLDER,
                video.filename
            )

            video.save(file_path)
            print(f"Video saved to: {file_path}")

        elif youtube_url:
            print(f"YouTube URL received: {youtube_url}")

            file_path = youtube_url

        else:
            print("Upload failed: no video file or YouTube URL provided")
            flash("Add a video file or YouTube URL before starting processing.", "error")
            return redirect("/dashboard")

        job_data = {

            "job_id": job_id,
            "job_slug": job_slug,
            "user": session["user"],
            "file": file_path,
            "status": "uploaded",
            "uploaded_at": datetime.now(timezone.utc),
            "queued_at": datetime.now(timezone.utc),
            "transcription_provider": transcription_provider,
            "deepgram_model": deepgram_model,
            "summary_model": None,
            "blog": None

        }

        jobs_collection.insert_one(job_data)
        print(f"Job created: {job_id} ({job_slug})")

        return redirect(f"/processing/{job_id}")
    return redirect("/dashboard")
