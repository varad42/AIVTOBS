import os
import json

from flask import Blueprint, render_template, send_file, redirect

from config import JOBS_FOLDER
from database.mongo import jobs_collection
from modules.pdf_generator import create_pdf
from modules.summarizer import build_timestamped_summary

blog_bp = Blueprint("blog", __name__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_path(path):

    if not path:
        return path

    if os.path.isabs(path):
        return path

    return os.path.join(PROJECT_ROOT, path)


def _get_job(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        return None, "Job not found"

    return job, None


def _read_text_file(path):

    resolved_path = _resolve_path(path)

    if not resolved_path or not os.path.exists(resolved_path):
        return None

    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            with open(resolved_path, "r", encoding=encoding) as file_handle:
                return file_handle.read()
        except UnicodeDecodeError:
            continue

    with open(resolved_path, "r", encoding="utf-8", errors="replace") as file_handle:
        return file_handle.read()


def _build_pdf_from_text(source_path, text):

    resolved_source_path = _resolve_path(source_path)
    pdf_path = os.path.splitext(resolved_source_path)[0] + ".pdf"
    create_pdf(text, pdf_path)
    return pdf_path


def _read_segments_file(path):

    resolved_path = _resolve_path(path)

    if not resolved_path or not os.path.exists(resolved_path):
        return None

    with open(resolved_path, "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _infer_segments_path(job):

    direct_path = job.get("segments_file")
    if direct_path:
        return direct_path

    job_slug = job.get("job_slug") or job.get("job_id")
    if not job_slug:
        return None

    return os.path.join(JOBS_FOLDER, f"{job_slug}_segments.json")


def _get_timestamped_summary(job, plain_summary_text):

    timestamped_path = job.get("summary_with_timestamps_file")
    timestamped_text = _read_text_file(timestamped_path)

    if timestamped_text:
        return timestamped_text, timestamped_path

    segments = _read_segments_file(_infer_segments_path(job))
    if not segments:
        return plain_summary_text, job.get("summary_file")

    timestamped_text = build_timestamped_summary(plain_summary_text, segments)

    if timestamped_path:
        with open(_resolve_path(timestamped_path), "w", encoding="utf-8") as file_handle:
            file_handle.write(timestamped_text)

    return timestamped_text, timestamped_path or job.get("summary_file")


@blog_bp.route("/summary/<job_id>")
def view_summary(job_id):

    job, error = _get_job(job_id)

    if error:
        return error

    summary_text = _read_text_file(job.get("summary_file"))
    timestamp_summary_text = _read_text_file(job.get("timestamp_summary_file"))

    if summary_text is None:
        return "Summary not ready"

    return render_template(
        "summary.html",
        summary=summary_text,
        timestamp_summary=timestamp_summary_text,
        job_id=job_id,
        model_name=job.get("summary_model", "t5")
    )


@blog_bp.route("/download_summary/<job_id>")
def download_summary(job_id):

    job, error = _get_job(job_id)

    if error:
        return error

    summary_text = _read_text_file(job.get("summary_file"))

    if summary_text is None:
        return "Summary not ready"

    summary_text, path = _get_timestamped_summary(job, summary_text)

    resolved_path = _resolve_path(path)

    if not resolved_path or not os.path.exists(resolved_path):
        return "Summary not ready"

    pdf_path = _build_pdf_from_text(path, summary_text)
    model_name = job.get("summary_model", "t5")

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{job_id}_summary_{model_name}.pdf"
    )


@blog_bp.route("/blog/<job_id>")
def view_blog(job_id):

    job, error = _get_job(job_id)

    if error:
        return error

    blog_text = _read_text_file(job.get("blog_file"))

    if blog_text is None:
        return "Blog not ready"

    return render_template(
        "blog.html",
        blog=blog_text,
        job_id=job_id,
        model_name=job.get("summary_model", "t5")
    )


@blog_bp.route("/generate_blog/<job_id>")
def generate_blog_for_job(job_id):

    job, error = _get_job(job_id)

    if error:
        return error

    if not job.get("summary_file"):
        return "Summary not ready"

    if job.get("blog_file"):
        return redirect(f"/blog/{job_id}")

    jobs_collection.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": "blog_requested"
            }
        }
    )

    return redirect(f"/processing/{job_id}")


@blog_bp.route("/download_blog/<job_id>")
def download_blog(job_id):

    job, error = _get_job(job_id)

    if error:
        return error

    path = job.get("blog_file")
    resolved_path = _resolve_path(path)

    if not resolved_path or not os.path.exists(resolved_path):
        return "Blog not ready"

    blog_text = _read_text_file(path)

    if blog_text is None:
        return "Blog not ready"

    pdf_path = _build_pdf_from_text(path, blog_text)
    model_name = job.get("summary_model", "t5")

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{job_id}_blog_{model_name}.pdf"
    )
