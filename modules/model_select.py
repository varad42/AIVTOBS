from flask import Blueprint, render_template, request, redirect
from database.mongo import jobs_collection

model_bp = Blueprint("model", __name__)


@model_bp.route("/select_model/<job_id>", methods=["GET", "POST"])
def select_model(job_id):

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        return "Job not found"

    if request.method == "POST":

        model = request.form["model"]

        jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "summary_model": model,
                    "status": "summarize_requested"
                },
                "$unset": {
                    "summary_file": ""
                }
            }
        )

        return redirect(f"/processing/{job_id}")

    return render_template("select_model.html", job=job)