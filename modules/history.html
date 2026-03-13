from flask import Blueprint, render_template, session, redirect
from database.mongo import jobs_collection

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history():

    if "user" not in session:
        return redirect("/")

    user = session["user"]

    jobs = jobs_collection.find({"user": user}).sort("_id", -1)

    return render_template("history.html", jobs=jobs)