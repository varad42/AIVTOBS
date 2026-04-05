from dotenv import load_dotenv
load_dotenv()
import threading
import os
from flask import Flask, render_template, session, redirect, request
from config import SECRET_KEY
from modules.model_select import model_bp
from modules.blog import blog_bp
from modules.history import history_bp
from database.mongo import jobs_collection

from auth.login import login_bp
from auth.register import register_bp
from auth.password_reset import password_reset_bp
from auth.google_auth import google_auth_bp
from modules.upload import upload_bp
from modules.processing import processing_bp


def create_app():

    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    app.register_blueprint(login_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(password_reset_bp)
    app.register_blueprint(google_auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(history_bp)

    @app.route("/dashboard")
    def dashboard():

        if "user" not in session:
            return render_template(
                "dashboard.html",
                show_login=True,
                email="",
                jobs=[],
                summary_ready_count=0,
                blog_ready_count=0
            )

        jobs = list(
            jobs_collection.find(
                {
                    "user": session["user"],
                    "status": {"$in": ["summary_ready", "blog_ready"]},
                }
            ).sort("_id", -1).limit(8)
        )
        summary_ready_count = sum(1 for job in jobs if job.get("summary_file"))
        blog_ready_count = sum(1 for job in jobs if job.get("blog_file"))
        active_job_id = request.args.get("job_id")
        active_job = None

        if active_job_id:
            active_job = jobs_collection.find_one(
                {"user": session["user"], "job_id": active_job_id}
            )

        if active_job is None and jobs:
            active_job = jobs[0]

        progress_map = {
            "uploading": 10,
            "uploaded": 15,
            "downloading": 20,
            "extracting_audio": 40,
            "transcribing": 60,
            "waiting_for_model": 80,
            "summarize_requested": 85,
            "blog_requested": 90,
            "summary_ready": 100,
            "blog_ready": 100,
        }
        active_progress = progress_map.get(
            active_job.get("status"),
            5
        ) if active_job else 0
        auto_refresh_statuses = {
            "uploading",
            "uploaded",
            "downloading",
            "extracting_audio",
            "transcribing",
            "waiting_for_model",
            "summarize_requested",
            "blog_requested",
        }
        should_auto_refresh = bool(
            active_job and active_job.get("status") in auto_refresh_statuses
        )

        return render_template(
            "dashboard.html",
            show_login=False,
            jobs=jobs,
            summary_ready_count=summary_ready_count,
            blog_ready_count=blog_ready_count,
            active_job=active_job,
            active_progress=active_progress,
            should_auto_refresh=should_auto_refresh
        )

    @app.route("/logout")
    def logout():

        session.clear()
        return redirect("/")

    return app


def start_background_services():
    from modules.queue_worker import (
        worker_loop,
        preload_whisper_model,
    )

    preload_thread = threading.Thread(target=preload_whisper_model, daemon=True)
    preload_thread.start()

    thread = threading.Thread(target=worker_loop, daemon=True)
    thread.start()


app = create_app()


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))

    # Prevent duplicate worker threads when Flask debug reloader is enabled.
    if (not debug) or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_background_services()

    app.run(host=host, port=port, debug=debug)
