from flask import Blueprint, render_template
from database.mongo import jobs_collection

processing_bp = Blueprint("processing", __name__)


@processing_bp.route("/processing/<job_id>")
def processing(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    return render_template("processing.html", job=job)