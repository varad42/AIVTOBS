from flask import Blueprint, render_template, request, redirect, session, flash
from database.mongo import users_collection
from flask_bcrypt import Bcrypt
from auth.utils import is_valid_email, normalize_email

login_bp = Blueprint("login", __name__)

bcrypt = Bcrypt()


@login_bp.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = normalize_email(request.form.get("email"))
        password = request.form.get("password", "")

        if not email or not password:
            flash("Enter both email and password before logging in.", "error")
            return render_template("login.html", email=email)

        if not is_valid_email(email):
            flash("That email address does not look valid. Check the format and try again.", "error")
            return render_template("login.html", email=email)

        user = users_collection.find_one({"email": email})
        stored_password = user.get("password") if user else None

        if user and stored_password and bcrypt.check_password_hash(stored_password, password):

            session["user"] = email
            return redirect("/dashboard")

        if not user:
            flash("No account was found for that email. Register first or try another email.", "error")
            return render_template("login.html", email=email)

        if user.get("auth_provider") == "google" and not stored_password:
            flash("This account uses Google sign-in. Click Continue with Google to log in.", "error")
            return render_template("login.html", email=email)

        flash("Incorrect password. Try again or use Forgot password to reset it.", "error")
        return render_template("login.html", email=email)

    return render_template("login.html", email="")
