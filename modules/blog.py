from flask import Blueprint, render_template
from flask import send_file
from modules.pdf_generator import create_pdf
from database.mongo import jobs_collection

blog_bp = Blueprint("blog", __name__)


@blog_bp.route("/blog/<job_id>")
def blog_page(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        return "Job not found"

    if "blog_file" not in job:
        return "Blog not ready"

    with open(job["blog_file"], "r", encoding="utf-8") as f:
        blog_text = f.read()

    return render_template(
        "blog.html",
        blog=blog_text,
        job_id=job_id,
        thumbnail=job.get("thumbnail")
    )

@blog_bp.route("/blog/<job_id>")
def view_blog(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        return "Job not found"

    blog_file = job.get("blog_file")

    blog = ""

    if blog_file:
        with open(blog_file, "r", encoding="utf-8") as f:
            blog = f.read()

    return render_template(
        "blog.html",
        blog=blog,
        job_id=job_id,
        thumbnail=job.get("thumbnail")
    )
from flask import send_file


@blog_bp.route("/download_blog/<job_id>")
def download_blog(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        return "Job not found"

    if "blog_file" not in job:
        return "Blog not ready"

    path = job["blog_file"]

    return send_file(
        path,
        as_attachment=True,
        download_name=f"{job_id}_blog.txt"
    )