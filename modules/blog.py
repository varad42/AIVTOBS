import os

from flask import Blueprint, render_template, send_file, redirect

from database.mongo import jobs_collection
from modules.pdf_generator import create_pdf

blog_bp = Blueprint("blog", __name__)


def _get_job(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        return None, "Job not found"

    return job, None


def _read_text_file(path):

    if not path or not os.path.exists(path):
        return None

    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as file_handle:
                return file_handle.read()
        except UnicodeDecodeError:
            continue

    with open(path, "r", encoding="utf-8", errors="replace") as file_handle:
        return file_handle.read()


def _build_pdf_from_text(source_path, text):

    pdf_path = os.path.splitext(source_path)[0] + ".pdf"
    create_pdf(text, pdf_path)
    return pdf_path


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

    path = job.get("summary_file")

    if not path or not os.path.exists(path):
        return "Summary not ready"

    summary_text = _read_text_file(path)

    if summary_text is None:
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

    if not path or not os.path.exists(path):
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
