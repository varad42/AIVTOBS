import whisper
import time
import os
import subprocess
import traceback
from datetime import datetime, timezone
from pymongo import ReturnDocument

from database.mongo import jobs_collection


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
            "status": "uploaded",
            "queued_at": {"$gte": worker_started_at}
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

        print("Processing job", job_id)

        file_path = job["file"]

        video_path = f"jobs/{job_id}"
        audio_path = f"jobs/{job_id}.wav"
        txt_path = f"jobs/{job_id}.txt"

        # -------------------
        # Download YouTube
        # -------------------

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

        # -------------------
        # Extract audio
        # -------------------

        print("Extracting audio")

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "extracting_audio"}}
        )

        extract_audio(video_path, audio_path)

        print("Audio created:", audio_path)

        # -------------------
        # Transcribe
        # -------------------

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "transcribing"}}
        )

        print("Starting Whisper")

        transcribe_audio(audio_path, txt_path)

        print("Transcript saved:", txt_path)

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "waiting_for_model","transcript_file": txt_path}}
        )

    except Exception as e:

        print("ERROR IN WORKER:", e)
        print(traceback.format_exc())

        jobs_collection.update_one(
            {"job_id": job["job_id"]},
            {"$set": {"status": "error", "error_message": str(e)}}
        )


def worker_loop():

    print("Worker started")
    worker_started_at = datetime.now(timezone.utc)

    while True:

        job = claim_next_job(worker_started_at)

        if job:
            process_job(job)

        time.sleep(3)
