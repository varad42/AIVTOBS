import time
import os
import subprocess
import traceback
import json
import re
import requests
import tempfile
import wave
import torch
from xml.etree.ElementTree import ParseError
from urllib.parse import parse_qs, urlparse

from datetime import datetime, timezone
from faster_whisper import WhisperModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import _errors as yta_errors

CouldNotRetrieveTranscript = yta_errors.CouldNotRetrieveTranscript
NoTranscriptFound = getattr(yta_errors, "NoTranscriptFound", CouldNotRetrieveTranscript)
RequestBlocked = getattr(yta_errors, "RequestBlocked", CouldNotRetrieveTranscript)
TranscriptsDisabled = getattr(yta_errors, "TranscriptsDisabled", CouldNotRetrieveTranscript)
VideoUnavailable = getattr(yta_errors, "VideoUnavailable", CouldNotRetrieveTranscript)
IpBlocked = getattr(yta_errors, "IpBlocked", RequestBlocked)

from config import YTDLP_COOKIES_FILE, YTDLP_COOKIES_FROM_BROWSER
from database.mongo import jobs_collection
from modules.blog_generator import generate_blog
from modules.summarizer import clean_transcript_text, summarize_section_text, summarize_text

_whisper_model_cache = {}
WHISPER_CHUNK_SECONDS = 420
TIMESTAMP_SUMMARY_SECTION_SECONDS = 300
TIMESTAMP_SUMMARY_MAX_CHARS = 2200


def get_whisper_runtime_config():

    if torch.cuda.is_available():
        return {
            "device": "cuda",
            "compute_type": "float16"
        }

    return {
        "device": "cpu",
        "compute_type": "int8"
    }


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

    return None


def fetch_youtube_transcript(video_url):

    video_id = extract_youtube_video_id(video_url)

    if not video_id:
        raise RuntimeError("Could not determine the YouTube video id from the URL.")

    try:
        try:
            transcript_segments = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
        except AttributeError:
            transcript_segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    except (
        CouldNotRetrieveTranscript,
        NoTranscriptFound,
        RequestBlocked,
        TranscriptsDisabled,
        VideoUnavailable,
        ParseError,
    ) as error:
        raise RuntimeError(f"YouTube transcript fetch failed: {error}") from error

    if not transcript_segments:
        raise RuntimeError("YouTube transcript response was empty.")

    normalized_segments = []
    transcript_parts = []

    for segment in transcript_segments:
        segment_text = " ".join(getattr(segment, "text", "").split()).strip()
        if not segment_text:
            continue

        start_time = float(getattr(segment, "start", 0.0))
        duration = float(getattr(segment, "duration", 0.0))
        end_time = start_time + max(duration, 0.0)

        normalized_segments.append(
            {
                "start": start_time,
                "end": end_time,
                "text": segment_text
            }
        )
        transcript_parts.append(segment_text)

    transcript_text = " ".join(transcript_parts).strip()

    if not transcript_text:
        raise RuntimeError("YouTube transcript text was empty after normalization.")

    return transcript_text, normalized_segments


def download_youtube(url, output):

    print(f"Downloading YouTube video from {url}")

    cmd = [
        "yt-dlp",
        "-o",
        output + ".%(ext)s",
    ]

    if YTDLP_COOKIES_FROM_BROWSER:
        print(f"Using yt-dlp cookies from browser: {YTDLP_COOKIES_FROM_BROWSER}")
        cmd.extend([
            "--cookies-from-browser",
            YTDLP_COOKIES_FROM_BROWSER
        ])
    elif YTDLP_COOKIES_FILE:
        print(f"Using yt-dlp cookies file: {YTDLP_COOKIES_FILE}")
        cmd.extend([
            "--cookies",
            YTDLP_COOKIES_FILE
        ])

    cmd.append(url)

    subprocess.run(cmd, check=True)

#123
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


def get_whisper_model(model_name="base"):

    if model_name not in _whisper_model_cache:
        runtime_config = get_whisper_runtime_config()
        print(
            f"Loading faster-whisper model into memory: {model_name} "
            f"on {runtime_config['device']} with {runtime_config['compute_type']}"
        )
        _whisper_model_cache[model_name] = WhisperModel(
            model_name,
            device=runtime_config["device"],
            compute_type=runtime_config["compute_type"]
        )

    return _whisper_model_cache[model_name]


def preload_whisper_model():

    try:
        print("Preloading faster-whisper model during app startup")
        get_whisper_model()
        print("faster-whisper model preloaded")
    except Exception as error:
        print(f"Failed to preload faster-whisper model: {error}")
        print(traceback.format_exc())


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


def transcribe_with_whisper(audio_path, language=None, task="transcribe", whisper_model_name="base", beam_size=1):

    print(f"Preparing faster-whisper transcription for audio: {audio_path}")
    model = get_whisper_model(whisper_model_name)
    audio_duration_seconds = get_wav_duration_seconds(audio_path)
    transcribe_kwargs = {
        "beam_size": beam_size,
        "task": task
    }

    if language:
        transcribe_kwargs["language"] = language

    print(
        f"Audio length is {audio_duration_seconds:.2f} seconds. "
        f"Transcribing in {WHISPER_CHUNK_SECONDS}-second chunks."
    )
    chunk_dir, chunk_paths = split_wav_into_chunks(audio_path)

    try:
        transcript_parts = []
        detected_info = None
        collected_segments = []

        for index, chunk_path in enumerate(chunk_paths, start=1):
            print(f"faster-whisper transcription started for chunk {index}/{len(chunk_paths)}")
            segments, info = model.transcribe(
                chunk_path,
                **transcribe_kwargs
            )
            if detected_info is None:
                detected_info = info

            chunk_offset_seconds = (index - 1) * WHISPER_CHUNK_SECONDS

            chunk_text_parts = []

            for segment in segments:
                segment_text = segment.text.strip()
                if not segment_text:
                    continue
                chunk_text_parts.append(segment_text)
                collected_segments.append(
                    {
                        "start": float(segment.start) + chunk_offset_seconds,
                        "end": float(segment.end) + chunk_offset_seconds,
                        "text": segment_text
                    }
                )

            chunk_text = " ".join(chunk_text_parts).strip()
            if chunk_text:
                transcript_parts.append(chunk_text)

        return " ".join(transcript_parts).strip(), detected_info, collected_segments
    finally:
        chunk_dir.cleanup()


def transcribe_audio(audio_path, txt_path, language=None, task="transcribe", whisper_model_name="base", beam_size=1):

    text, info, segments = transcribe_with_whisper(
        audio_path,
        language=language,
        task=task,
        whisper_model_name=whisper_model_name,
        beam_size=beam_size
    )

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Transcript saved to {txt_path}")
    return info, segments


def save_text_file(path, text):

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read_text_file(path):

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def format_timestamp(seconds):

    total_seconds = max(0, int(seconds))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

    return f"{minutes:02d}:{remaining_seconds:02d}"


def build_timed_summary_sections(segments):

    if not segments:
        return []

    sections = []
    current_section = None

    for segment in segments:
        segment_text = segment.get("text", "").strip()
        if not segment_text:
            continue

        segment_start = float(segment.get("start", 0.0))
        segment_end = float(segment.get("end", segment_start))

        should_start_new_section = False

        if current_section is None:
            should_start_new_section = True
        else:
            section_duration = segment_end - current_section["start"]
            projected_length = len(current_section["text"]) + 1 + len(segment_text)
            if (
                section_duration >= TIMESTAMP_SUMMARY_SECTION_SECONDS
                and projected_length >= 600
            ) or projected_length > TIMESTAMP_SUMMARY_MAX_CHARS:
                should_start_new_section = True

        if should_start_new_section:
            current_section = {
                "start": segment_start,
                "end": segment_end,
                "parts": [segment_text],
                "text": segment_text
            }
            sections.append(current_section)
            continue

        current_section["end"] = segment_end
        current_section["parts"].append(segment_text)
        current_section["text"] = " ".join(current_section["parts"])

    return sections


def build_timestamp_summary_text(sections, model_name):

    output_lines = []

    for section in sections:
        section_text = section["text"].strip()
        if not section_text:
            continue

        summary_input = section_text

        try:
            section_summary = summarize_section_text(summary_input, model_name)
        except Exception as error:
            print(f"Timestamp summary failed for section at {section['start']:.2f}s: {error}")
            section_summary = clean_transcript_text(summary_input)

        section_summary = re.sub(r"\[\d{1,2}:\d{2}(?::\d{2})?\]\s*", "", section_summary)
        section_summary = re.sub(r"(?:(?<=^)|(?<=\s))\d{1,2}:\d{2}(?::\d{2})?\s*-\s*", "", section_summary)
        section_summary = " ".join(section_summary.split())
        if not section_summary:
            continue

        output_lines.append(
            f"{format_timestamp(section['start'])} - {section_summary}"
        )

    return "\n".join(output_lines).strip()


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
        }
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

            cleaned_text = clean_transcript_text(text)
            cleaned_text_path = f"jobs/{job_file_stem}_cleaned.txt"

            print(f"Saving cleaned transcript for job {job_id} to {cleaned_text_path}")

            with open(cleaned_text_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)

            model = job.get(
                "summary_model",
                "t5"
            )

            summary = ""
            segments_path = job.get("transcript_segments_file")

            if segments_path and os.path.exists(segments_path):
                try:
                    with open(segments_path, "r", encoding="utf-8") as f:
                        transcript_segments = json.load(f)

                    timestamp_sections = build_timed_summary_sections(transcript_segments)
                    timestamp_summary_text = build_timestamp_summary_text(
                        timestamp_sections,
                        model
                    )

                    if timestamp_summary_text:
                        summary = timestamp_summary_text
                except Exception as error:
                    print(f"Timestamp summary generation failed for job {job_id}: {error}")
                    print(traceback.format_exc())

            if not summary:
                summary = summarize_text(
                    cleaned_text,
                    model
                )

            out = f"jobs/{job_file_stem}_summary_{model}.txt"
            print(f"Saving summary for job {job_id} using model {model} to {out}")
            save_text_file(out, summary)

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
                        "cleaned_transcript_file": cleaned_text_path,
                        "summary_file": out,
                        "timestamp_summary_file": None,
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

        if job["status"] == "blog_requested":
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

            jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": "blog_ready",
                        "model_used": model,
                        "blog_file": blog_path
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
        segments_path = f"jobs/{job_file_stem}_segments.json"
        download_seconds = None
        audio_extraction_seconds = None
        transcription_seconds = None

        if file_path.startswith("http"):
            print(f"Job {job_id} is a YouTube URL")

            jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {"status": "downloading"}}
            )

            transcript_started_at = time.perf_counter()

            try:
                print(f"Trying YouTube transcript fetch first for job {job_id}")
                transcript_text, transcript_segments = fetch_youtube_transcript(file_path)
                save_text_file(txt_path, transcript_text)
                save_text_file(
                    segments_path,
                    json.dumps(transcript_segments, ensure_ascii=False, indent=2)
                )
                transcription_seconds = time.perf_counter() - transcript_started_at

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
                            "original_transcript_file": txt_path,
                            "transcript_segments_file": segments_path,
                            "transcript_saved_at": transcript_saved_at,
                            "download_seconds": download_seconds,
                            "audio_extraction_seconds": None,
                            "transcription_seconds": transcription_seconds,
                            "upload_to_transcript_seconds": upload_to_transcript_seconds,
                            "transcription_provider": "youtube_transcript_api"
                        }
                    }
                )

                print(f"YouTube transcript ready for job {job_id}")
                print(f"YouTube caption transcript time: {transcription_seconds:.2f} seconds")
                if upload_to_transcript_seconds is not None:
                    print(
                        f"Time from upload/YouTube URL to transcript saved: "
                        f"{upload_to_transcript_seconds:.2f} seconds"
                    )
                return
            except (
                CouldNotRetrieveTranscript,
                IpBlocked,
                NoTranscriptFound,
                RequestBlocked,
                TranscriptsDisabled,
                VideoUnavailable,
                RuntimeError,
            ) as error:
                print(f"YouTube transcript unavailable for job {job_id}, falling back to Whisper: {error}")

            download_started_at = time.perf_counter()
            try:
                download_youtube(
                    file_path,
                    video_path
                )
            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    "YouTube transcript was unavailable, and the fallback video download was blocked by YouTube. "
                    "This usually happens because of rate limiting or bot verification. "
                    "Try again later, use another video, or provide the video file directly."
                ) from error

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
                    "transcription_provider": "whisper"
                }
            }
        )

        transcription_started_at = time.perf_counter()
        transcription_info, transcript_segments = transcribe_audio(
            audio_path,
            txt_path,
            language="en",
            task="transcribe",
            whisper_model_name="base",
            beam_size=1
        )
        save_text_file(
            segments_path,
            json.dumps(transcript_segments, ensure_ascii=False, indent=2)
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

        transcript_file_for_summary = txt_path
        original_transcript_file = txt_path

        jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "waiting_for_model",
                    "transcript_file": transcript_file_for_summary,
                    "original_transcript_file": original_transcript_file,
                    "transcript_segments_file": segments_path,
                    "transcript_saved_at": transcript_saved_at,
                    "download_seconds": download_seconds,
                    "audio_extraction_seconds": audio_extraction_seconds,
                    "transcription_seconds": transcription_seconds,
                    "upload_to_transcript_seconds": upload_to_transcript_seconds,
                    "transcription_provider": "whisper",
                    "whisper_model_used": "base",
                    "whisper_beam_size": 1,
                    "detected_language": getattr(transcription_info, "language", None)
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
                {"status": "blog_requested"}
            )

        if job:
            print(
                f"Worker picked job {job['job_id']} with status {job['status']}"
            )
            process_job(job)

        time.sleep(3)
