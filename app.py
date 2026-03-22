from dotenv import load_dotenv
load_dotenv()
from modules.queue_worker import worker_loop, preload_whisper_model, recover_interrupted_jobs
import threading
import os
from flask import Flask, render_template, session, redirect
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

    jobs = list(jobs_collection.find({"user": session["user"]}).sort("_id", -1).limit(8))
    summary_ready_count = sum(1 for job in jobs if job.get("summary_file"))
    blog_ready_count = sum(1 for job in jobs if job.get("blog_file"))

    return render_template(
        "dashboard.html",
        show_login=False,
        jobs=jobs,
        summary_ready_count=summary_ready_count,
        blog_ready_count=blog_ready_count
    )


@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")

    
if __name__ == "__main__":
    debug = True

    # Prevent duplicate worker threads when Flask debug reloader is enabled.
    if (not debug) or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        recover_interrupted_jobs()

        preload_thread = threading.Thread(target=preload_whisper_model, daemon=True)
        preload_thread.start()

        thread = threading.Thread(target=worker_loop, daemon=True)
        thread.start()

    app.run(debug=debug)
