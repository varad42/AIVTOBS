import time
import os
import subprocess
import traceback
import json

from datetime import datetime, timezone
from faster_whisper import WhisperModel
from pymongo import ReturnDocument

from database.mongo import jobs_collection
from modules.blog_generator import generate_blog
from modules.summarizer import summarize_text
from modules.thumbnail_generator import generate_thumbnail


def parse_utc_datetime(value):

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None

    return None


def get_job_file_stem(job):

    return job.get("job_slug") or job["job_id"]


def download_youtube(url, output):

    print(f"Downloading YouTube video from {url}")

    cmd = [
        "yt-dlp",
        "-o",
        output + ".%(ext)s",
        url
    ]

    subprocess.run(cmd, check=True)


def extract_audio(video, audio):

    print(f"Extracting audio from {video} to {audio}")

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

    print(f"Loading faster-whisper model for audio: {audio_path}")

    model = WhisperModel(
        "base",
        device="cpu",
        compute_type="int8"
    )

    print("faster-whisper transcription started")
    segments, info = model.transcribe(
        audio_path,
        beam_size=1
    )

    text = " ".join(segment.text.strip() for segment in segments).strip()

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Transcript saved to {txt_path}")


def claim_next_job(worker_started_at):

    print("Checking for next uploaded job")
    return jobs_collection.find_one_and_update(
        {
            "status": "uploaded"
        },
        {
            "$set": {
                "status": "processing"
            }
        },
        return_document=ReturnDocument.AFTER
    )


def process_job(job):

    try:

        job_id = job["job_id"]
        job_file_stem = get_job_file_stem(job)

        # ---------- summarize ----------

        if job["status"] == "summarize_requested":
            print(f"Summary generation started for job {job_id}")

            with open(
                job["transcript_file"],
                "r",
                encoding="utf-8"
            ) as f:

                text = f.read()

            model = job.get(
                "summary_model",
                "t5"
            )

            summary = summarize_text(
                text,
                model
            )

            out = f"jobs/{job_file_stem}_summary_{model}.txt"
            print(f"Saving summary for job {job_id} using model {model} to {out}")

            with open(out, "w") as f:
                f.write(summary)

            summary_saved_at = datetime.now(timezone.utc)
            model_selected_at = parse_utc_datetime(job.get("model_selected_at"))
            summary_generation_seconds = None

            if model_selected_at:
                summary_generation_seconds = (
                    summary_saved_at - model_selected_at
                ).total_seconds()

            jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": "summary_ready",
                        "summary_file": out,
                        "summary_saved_at": summary_saved_at,
                        "summary_generation_seconds": summary_generation_seconds
                    }
                }
            )

            print(f"Summary ready for job {job_id}")
            if summary_generation_seconds is not None:
                print(
                    f"Time from model selection to summary saved: "
                    f"{summary_generation_seconds:.2f} seconds"
                )

            return

        if job["status"] == "summary_ready":
            print(f"Blog generation started for job {job_id}")

            with open(
                job["summary_file"],
                "r",
                encoding="utf-8"
            ) as f:
                summary = f.read()

            blog = generate_blog(summary)
            blog_path = f"jobs/{job_file_stem}_blog.txt"

            with open(blog_path, "w", encoding="utf-8") as f:
                f.write(blog)

            title = blog.split("\n")[0].strip() or "Auto Generated Blog"
            thumb_path = f"jobs/{job_file_stem}_thumb.png"
            generate_thumbnail(title, thumb_path)

            jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": "blog_ready",
                        "blog_file": blog_path,
                        "thumbnail": thumb_path
                    }
                }
            )

            print(f"Blog ready for job {job_id}")
            return

        # ---------- normal ----------

        print(f"Processing pipeline started for job {job_id}")

        file_path = job["file"]

        video_path = f"jobs/{job_file_stem}"
        audio_path = f"jobs/{job_file_stem}.wav"
        txt_path = f"jobs/{job_file_stem}.txt"

        if file_path.startswith("http"):
            print(f"Job {job_id} is a YouTube URL")

            jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {"status": "downloading"}}
            )

            download_youtube(
                file_path,
                video_path
            )

            import glob

            files = glob.glob(
                f"jobs/{job_file_stem}.*"
            )

            for f in files:
                if f.endswith(".mp4") or f.endswith(".webm"):
                    video_path = f
                    print(f"Downloaded video path resolved to {video_path}")
                    break

        else:
            video_path = file_path
            print(f"Job {job_id} is using uploaded file {video_path}")

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "extracting_audio"}}
        )

        extract_audio(
            video_path,
            audio_path
        )

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "transcribing"}}
        )

        transcribe_audio(
            audio_path,
            txt_path
        )

        transcript_saved_at = datetime.now(timezone.utc)
        uploaded_at = parse_utc_datetime(job.get("uploaded_at"))
        upload_to_transcript_seconds = None

        if uploaded_at:
            upload_to_transcript_seconds = (
                transcript_saved_at - uploaded_at
            ).total_seconds()

        jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "waiting_for_model",
                    "transcript_file": txt_path,
                    "transcript_saved_at": transcript_saved_at,
                    "upload_to_transcript_seconds": upload_to_transcript_seconds
                }
            }
        )

        print(f"Transcript ready for job {job_id}")
        if upload_to_transcript_seconds is not None:
            print(
                f"Time from upload/YouTube URL to transcript saved: "
                f"{upload_to_transcript_seconds:.2f} seconds"
            )

    except Exception as e:

        print(f"ERROR in job {job.get('job_id')}: {e}")
        print(traceback.format_exc())

        jobs_collection.update_one(
            {"job_id": job["job_id"]},
            {
                "$set": {
                    "status": "error",
                    "error_message": str(e)
                }
            }
        )


def worker_loop():

    print("Worker started")

    worker_started_at = datetime.now(timezone.utc)

    while True:

        job = claim_next_job(
            worker_started_at
        )

        if not job:
            job = jobs_collection.find_one(
                {"status": "summarize_requested"}
            )

        if not job:
            job = jobs_collection.find_one(
                {"status": "summary_ready"}
            )

        if job:
            print(
                f"Worker picked job {job['job_id']} with status {job['status']}"
            )
            process_job(job)

        time.sleep(3)
