import time
import os
import subprocess
import traceback
import json
import requests
import tempfile
import wave

from datetime import datetime, timezone
from faster_whisper import WhisperModel
from pymongo import ReturnDocument

from config import DEEPGRAM_API_KEY
from database.mongo import jobs_collection
from modules.blog_generator import generate_blog
from modules.summarizer import summarize_text
from modules.thumbnail_generator import generate_thumbnail

_whisper_model = None
WHISPER_CHUNK_SECONDS = 420
WHISPER_CHUNK_THRESHOLD_SECONDS = 1200


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


def get_whisper_model():

    global _whisper_model

    if _whisper_model is None:
        print("Loading faster-whisper model into memory")
        _whisper_model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )

    return _whisper_model


def get_wav_duration_seconds(audio_path):

    with wave.open(audio_path, "rb") as wav_file:
        frame_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()

    if not frame_rate:
        return 0

    return frame_count / float(frame_rate)


def split_wav_into_chunks(audio_path, chunk_seconds=WHISPER_CHUNK_SECONDS):

    temp_dir = tempfile.TemporaryDirectory(prefix="whisper_chunks_")
    chunk_pattern = os.path.join(temp_dir.name, "chunk_%03d.wav")

    cmd = [
        "ffmpeg",
        "-i", audio_path,
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        "-ac", "1",
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        chunk_pattern,
        "-y"
    ]

    subprocess.run(cmd, check=True)

    chunk_paths = sorted(
        os.path.join(temp_dir.name, file_name)
        for file_name in os.listdir(temp_dir.name)
        if file_name.endswith(".wav")
    )

    return temp_dir, chunk_paths


def transcribe_with_whisper(audio_path):

    print(f"Preparing faster-whisper transcription for audio: {audio_path}")
    model = get_whisper_model()
    audio_duration_seconds = get_wav_duration_seconds(audio_path)

    if audio_duration_seconds <= WHISPER_CHUNK_THRESHOLD_SECONDS:
        print("faster-whisper transcription started")
        segments, info = model.transcribe(
            audio_path,
            beam_size=1
        )

        return " ".join(segment.text.strip() for segment in segments).strip()

    print(
        f"Long audio detected ({audio_duration_seconds:.2f} seconds). "
        f"Transcribing in {WHISPER_CHUNK_SECONDS}-second chunks."
    )
    chunk_dir, chunk_paths = split_wav_into_chunks(audio_path)

    try:
        transcript_parts = []

        for index, chunk_path in enumerate(chunk_paths, start=1):
            print(f"faster-whisper transcription started for chunk {index}/{len(chunk_paths)}")
            segments, info = model.transcribe(
                chunk_path,
                beam_size=1
            )

            chunk_text = " ".join(segment.text.strip() for segment in segments).strip()
            if chunk_text:
                transcript_parts.append(chunk_text)

        return " ".join(transcript_parts).strip()
    finally:
        chunk_dir.cleanup()


def transcribe_with_deepgram(audio_path, model_name="nova-3"):

    if not DEEPGRAM_API_KEY:
        raise RuntimeError("Deepgram provider selected but DEEPGRAM_API_KEY is not configured.")

    print(f"Deepgram transcription started for audio: {audio_path}")

    with open(audio_path, "rb") as audio_file:
        response = requests.post(
            "https://api.deepgram.com/v1/listen",
            params={
                "model": model_name,
                "smart_format": "true"
            },
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav"
            },
            data=audio_file,
            timeout=300
        )

    response.raise_for_status()
    data = response.json()

    try:
        return data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("Deepgram transcription response did not include a transcript.") from error


def transcribe_audio(audio_path, txt_path, provider="whisper", deepgram_model="nova-3"):

    if provider == "deepgram":
        text = transcribe_with_deepgram(audio_path, deepgram_model)
    else:
        text = transcribe_with_whisper(audio_path)

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
                        "model_used": model,
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
            model = job.get("summary_model", "t5")
            blog_path = f"jobs/{job_file_stem}_blog_{model}.txt"

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
                        "model_used": model,
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
        provider = job.get("transcription_provider", "whisper")
        deepgram_model = job.get("deepgram_model", "nova-3")

        video_path = f"jobs/{job_file_stem}"
        audio_path = f"jobs/{job_file_stem}.wav"
        txt_path = f"jobs/{job_file_stem}.txt"
        download_seconds = None
        audio_extraction_seconds = None
        transcription_seconds = None

        if file_path.startswith("http"):
            print(f"Job {job_id} is a YouTube URL")

            jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {"status": "downloading"}}
            )

            download_started_at = time.perf_counter()
            download_youtube(
                file_path,
                video_path
            )
            download_seconds = time.perf_counter() - download_started_at
            jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "download_seconds": download_seconds
                    }
                }
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

        audio_extraction_started_at = time.perf_counter()
        extract_audio(
            video_path,
            audio_path
        )
        audio_extraction_seconds = time.perf_counter() - audio_extraction_started_at
        jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "audio_extraction_seconds": audio_extraction_seconds
                }
            }
        )

        jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "transcribing",
                    "transcription_provider": provider,
                    "deepgram_model": deepgram_model
                }
            }
        )

        transcription_started_at = time.perf_counter()
        transcribe_audio(
            audio_path,
            txt_path,
            provider,
            deepgram_model
        )
        transcription_seconds = time.perf_counter() - transcription_started_at
        jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "transcription_seconds": transcription_seconds
                }
            }
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
                    "download_seconds": download_seconds,
                    "audio_extraction_seconds": audio_extraction_seconds,
                    "transcription_seconds": transcription_seconds,
                    "upload_to_transcript_seconds": upload_to_transcript_seconds,
                    "transcription_provider": provider,
                    "deepgram_model": deepgram_model
                }
            }
        )

        print(f"Transcript ready for job {job_id}")
        if download_seconds is not None:
            print(f"YouTube download time: {download_seconds:.2f} seconds")
        if audio_extraction_seconds is not None:
            print(f"Audio extraction time: {audio_extraction_seconds:.2f} seconds")
        if transcription_seconds is not None:
            print(f"Transcription time: {transcription_seconds:.2f} seconds")
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
