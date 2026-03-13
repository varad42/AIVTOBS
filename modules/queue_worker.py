import whisper
import time
import os
import subprocess
import traceback
from datetime import datetime, timezone
from pymongo import ReturnDocument
from modules.thumbnail_generator import generate_thumbnail
import subprocess
import json





from database.mongo import jobs_collection
from modules.summarizer import summarize_text
from modules.blog_generator import generate_blog

def get_video_duration(path):

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("ffprobe error:", result.stderr)
        return 0

    try:
        data = json.loads(result.stdout)

        if "format" not in data:
            print("No format in ffprobe output")
            return 0

        duration = float(data["format"]["duration"])

        return duration

    except Exception as e:
        print("Duration read error:", e)
        return 0

def download_youtube(url, output):

    cmd = [
        "yt-dlp",
        "-o",
        output + ".%(ext)s",
        url
    ]

    subprocess.run(cmd, check=True)


def extract_audio(video, audio):

    cmd = [
        "ffmpeg",
        "-i", video,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        "-acodec", "pcm_s16le",
        audio,
        "-y"
    ]

    subprocess.run(cmd, check=True)

def transcribe_audio(audio_path, txt_path):

    print("Loading Whisper model")

    model = whisper.load_model("base")

    print("Transcribing")

    result = model.transcribe(audio_path, fp16=False)

    text = result.get("text", "").strip()

    os.makedirs(os.path.dirname(txt_path), exist_ok=True)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    if not os.path.exists(txt_path):
        raise RuntimeError(f"Transcript file was not created: {txt_path}")

    if os.path.getsize(txt_path) == 0:
        print("Warning: transcript is empty")


def claim_next_job(worker_started_at):

    return jobs_collection.find_one_and_update(
        {
            "status": "uploaded"
        },
        {
            "$set": {
                "status": "processing",
                "started_at": datetime.now(timezone.utc).isoformat()
            }
        },
        return_document=ReturnDocument.AFTER
    )


def process_job(job):

    try:

        job_id = job["job_id"]
        status = job["status"]

        # =========================
        # SUMMARY STEP
        # =========================

        if status == "summarize_requested":

            print("Summarizing", job_id)

            txt = job["transcript_file"]

            with open(txt, "r", encoding="utf-8") as f:
                text = f.read()

            model = job.get("summary_model", "t5")

            summary = summarize_text(text, model)

            out = f"jobs/{job_id}_summary_{model}.txt"

            if os.path.exists(out):
                os.remove(out)

            with open(out, "w", encoding="utf-8") as f:
                f.write(summary)

            jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "summary_ready",
                    "summary_file": out
                }}
            )

            return


        # =========================
        # BLOG STEP
        # =========================

        if status == "summary_ready":

            print("Generating blog", job_id)

            with open(job["summary_file"], "r", encoding="utf-8") as f:
                summary = f.read()

            blog = generate_blog(summary)

            blog_path = f"jobs/{job_id}_blog.txt"

            with open(blog_path, "w", encoding="utf-8") as f:
                f.write(blog)

            # get title from blog
            title = blog.split("\n")[0]

            thumb_path = f"jobs/{job_id}_thumb.png"

            generate_thumbnail(title, thumb_path)

            jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "blog_ready",
                    "blog_file": blog_path,
                    "thumbnail": thumb_path
                }}
            )

            return


        # =========================
        # NORMAL PIPELINE ONLY FOR NEW JOBS
        # =========================

        if status not in [
            "uploaded",
            "processing",
            "downloading",
            "extracting_audio",
            "transcribing"
        ]:
            return


        print("Processing job", job_id)

        file_path = job["file"]

        video_path = f"jobs/{job_id}"
        
        duration = get_video_duration(video_path)

        print("Duration:", duration)

        MAX_DURATION = 7200

        if duration and duration > MAX_DURATION:

            jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "error",
                    "error_message": "Video too long (max 2 hours)"
                }}
            )

            return
        audio_path = f"jobs/{job_id}.wav"
        txt_path = f"jobs/{job_id}.txt"


        # ---- download ----

        if file_path.startswith("http"):

            jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {"status": "downloading"}}
            )

            download_youtube(file_path, video_path)

            import glob

            files = glob.glob(f"jobs/{job_id}.*")

            for f in files:
                if f.endswith(".mp4") or f.endswith(".webm") or f.endswith(".mkv"):
                    video_path = f
                    break

        else:
            video_path = file_path


        # ---- extract ----

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "extracting_audio"}}
        )

        extract_audio(video_path, audio_path)


        # ---- transcribe ----

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "transcribing"}}
        )

        transcribe_audio(audio_path, txt_path)


        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "waiting_for_model",
                "transcript_file": txt_path
            }}
        )


    except Exception as e:

        print("ERROR IN WORKER:", e)
        print(traceback.format_exc())

        jobs_collection.update_one(
            {"job_id": job["job_id"]},
            {"$set": {
                "status": "error",
                "error_message": str(e)
            }}
        )


def worker_loop():

    print("Worker started")

    worker_started_at = datetime.now(timezone.utc)

    while True:

        job = None

        job = claim_next_job(worker_started_at)

        if not job:
            job = jobs_collection.find_one({"status": "summarize_requested"})

        if not job:
            job = jobs_collection.find_one({"status": "summary_ready"})

        if not job:
            job = jobs_collection.find_one({"status": "waiting_for_model"})

        if job:
            process_job(job)

        time.sleep(2)