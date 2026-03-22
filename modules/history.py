from datetime import datetime, timezone
from flask import Blueprint, render_template, session, redirect, request, flash
from database.mongo import jobs_collection

history_bp = Blueprint("history", __name__)
TERMINAL_JOB_STATUSES = {"blog_ready", "canceled", "error"}


@history_bp.route("/history")
def history():

    if "user" not in session:
        return redirect("/")

    user = session["user"]

    jobs = jobs_collection.find({"user": user}).sort("_id", -1)

    return render_template("history.html", jobs=jobs)


@history_bp.route("/cancel_job/<job_id>", methods=["POST"])
def cancel_job(job_id):

    if "user" not in session:
        return redirect("/")

    job = jobs_collection.find_one(
        {
            "job_id": job_id,
            "user": session["user"]
        }
    )

    if not job:
        flash("Job not found.", "error")
        return redirect("/history")

    if job.get("status") in TERMINAL_JOB_STATUSES:
        flash("This job is already finished and cannot be canceled.", "info")
        return redirect("/history")

    jobs_collection.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": "canceled",
                "canceled_at": datetime.now(timezone.utc)
            }
        }
    )

    flash("Job canceled.", "info")
    return redirect(request.referrer or "/history")
