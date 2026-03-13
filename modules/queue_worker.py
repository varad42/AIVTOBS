import whisper
import time
import os
import subprocess
import traceback
from datetime import datetime, timezone
from pymongo import ReturnDocument


from database.mongo import jobs_collection
from modules.summarizer import summarize_text
from modules.blog_generator import generate_blog

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


def claim_next_job():

    return jobs_collection.find_one_and_update(
        {"status": "uploaded"},
        {"$set": {"status": "processing"}},
        return_document=ReturnDocument.AFTER
    )


def process_job(job):

    try:

        job_id = job["job_id"]

        # =========================
        # SUMMARY STEP
        # =========================

        if job["status"] == "summarize_requested":

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
        if job["status"] == "summary_ready":

            job_id = job["job_id"]

            print("Generating blog", job_id)

            summary_file = job["summary_file"]

            with open(summary_file, "r", encoding="utf-8") as f:
                summary = f.read()

            blog = generate_blog(summary)

            blog_path = f"jobs/{job_id}_blog.txt"

            with open(blog_path, "w", encoding="utf-8") as f:
                f.write(blog)

            jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "blog_ready",
                    "blog_file": blog_path
                }}
            )

            return



        # =========================
        # NORMAL PIPELINE
        # =========================

        print("Processing job", job_id)

        file_path = job["file"]

        video_path = f"jobs/{job_id}"
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

        print("Extracting audio")

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "extracting_audio"}}
        )

        extract_audio(video_path, audio_path)

        print("Audio created:", audio_path)


        # ---- transcribe ----

        jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "transcribing"}}
        )

        transcribe_audio(audio_path, txt_path)

        print("Transcript saved:", txt_path)

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
            {"$set": {"status": "error", "error_message": str(e)}}
        )


def worker_loop():

    print("Worker started")

    while True:

        job = claim_next_job()

        if not job:
            job = jobs_collection.find_one({"status": "summarize_requested"})

        if not job:
            job = jobs_collection.find_one({"status": "summary_ready"})

        if job:
            process_job(job)

        time.sleep(3)