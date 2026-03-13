from flask import Blueprint, render_template, request, redirect, session
import os
import uuid
from datetime import datetime, timezone

from config import UPLOAD_FOLDER
from database.mongo import jobs_collection

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload", methods=["GET", "POST"])
def upload():

    print("UPLOAD ROUTE CALLED")

    if "user" not in session:
        print("No session")
        return redirect("/")

    if request.method == "POST":

        print("POST received")

        video = request.files.get("video")
        youtube_url = request.form.get("youtube")

        job_id = str(uuid.uuid4())

        file_path = ""

        if video and video.filename != "":
            print("Video upload detected")

            file_path = os.path.join(UPLOAD_FOLDER, video.filename)

            video.save(file_path)

        elif youtube_url:
            print("YouTube URL detected")

            file_path = youtube_url

        else:
            print("No input")
            return "No input"

        job_data = {
            "job_id": job_id,
            "user": session["user"],
            "file": file_path,
            "status": "uploaded",
            "queued_at": datetime.now(timezone.utc),
            "summary_model": None,
            "blog": None
        }

        print("Inserting job:", job_data)

        jobs_collection.insert_one(job_data)

        print("Inserted")

        return redirect(f"/processing/{job_id}")

    return render_template("upload.html")
