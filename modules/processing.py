from flask import Blueprint, render_template
from database.mongo import jobs_collection

processing_bp = Blueprint("processing", __name__)


def format_seconds(value):

    if value is None:
        return None

    try:
        return f"{float(value):.2f} seconds"
    except (TypeError, ValueError):
        return None


@processing_bp.route("/processing/<job_id>")
def processing(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        return "Job not found"

    return render_template(
        "processing.html",
        job=job,
        format_seconds=format_seconds
    )
