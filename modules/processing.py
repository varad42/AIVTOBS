from flask import Blueprint, redirect

processing_bp = Blueprint("processing", __name__)


@processing_bp.route("/processing/<job_id>")
def processing(job_id):
    return redirect(f"/dashboard?job_id={job_id}")
