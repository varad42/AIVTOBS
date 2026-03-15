from flask import Blueprint, render_template, request, redirect, session
import os
import re
import uuid
from urllib.parse import urlparse
from datetime import datetime, timezone

from config import UPLOAD_FOLDER
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

    if request.method == "POST":

        video = request.files.get("video")
        youtube_url = request.form.get("youtube")

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
            return "No input"

        job_data = {

            "job_id": job_id,
            "job_slug": job_slug,
            "user": session["user"],
            "file": file_path,
            "status": "uploaded",
            "uploaded_at": datetime.now(timezone.utc),
            "queued_at": datetime.now(timezone.utc),
            "summary_model": None,
            "blog": None

        }

        jobs_collection.insert_one(job_data)
        print(f"Job created: {job_id} ({job_slug})")

        return redirect(f"/processing/{job_id}")

    return render_template("upload.html")
