from modules.queue_worker import worker_loop
import threading
import os
from flask import Flask, render_template, session, redirect
from config import SECRET_KEY
from modules.model_select import model_bp
from modules.blog import blog_bp
from modules.history import history_bp

from auth.login import login_bp
from auth.register import register_bp
from modules.upload import upload_bp
from modules.processing import processing_bp
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(login_bp)
app.register_blueprint(register_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(processing_bp)
app.register_blueprint(model_bp)
app.register_blueprint(blog_bp)
app.register_blueprint(history_bp)

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html")


if __name__ == "__main__":
    debug = True

    # Prevent duplicate worker threads when Flask debug reloader is enabled.
    if (not debug) or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        thread = threading.Thread(target=worker_loop, daemon=True)
        thread.start()

    app.run(debug=debug)
