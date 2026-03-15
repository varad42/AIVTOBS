from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect
from database.mongo import jobs_collection

model_bp = Blueprint("model", __name__)


@model_bp.route("/select_model/<job_id>", methods=["GET", "POST"])
def select_model(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        print(f"Model selection failed: job {job_id} not found")
        return "Job not found"

    if request.method == "POST":

        model = request.form.get("model")
        print(f"Model selected for job {job_id}: {model}")

        jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "summary_model": model,
                    "status": "summarize_requested",
                    "model_selected_at": datetime.now(timezone.utc)
                }
            }
        )

        return redirect(f"/processing/{job_id}")

    return render_template(
        "select_model.html",
        job=job
    )
