from flask import Blueprint, render_template, session, redirect
from database.mongo import jobs_collection

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history():

    if "user" not in session:
        return redirect("/")

    user = session["user"]

    jobs = jobs_collection.find(
        {
            "user": user,
            "status": {
                "$in": [
                    "uploading",
                    "uploaded",
                    "processing",
                    "downloading",
                    "extracting_audio",
                    "transcribing",
                    "waiting_for_model",
                    "summarize_requested",
                    "summary_ready",
                    "blog_requested",
                    "blog_ready",
                    "error",
                ]
            },
        }
    ).sort("_id", -1)

    return render_template("history.html", jobs=jobs)
