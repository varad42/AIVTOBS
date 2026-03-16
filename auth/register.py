from flask import Blueprint, render_template, request, redirect, flash
from database.mongo import users_collection
from flask_bcrypt import Bcrypt
from auth.utils import is_valid_email, normalize_email, validate_password

register_bp = Blueprint("register", __name__)

bcrypt = Bcrypt()


@register_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = normalize_email(request.form.get("email"))
        password = request.form.get("password", "")

        if not email or not password:
            flash("Enter an email and password to create your account.", "error")
            return render_template("register.html", email=email)

        if not is_valid_email(email):
            flash("Please enter a valid email address, for example `name@example.com`.", "error")
            return render_template("register.html", email=email)

        password_error = validate_password(password)
        if password_error:
            flash(f"{password_error} Add a stronger password and try again.", "error")
            return render_template("register.html", email=email)

        if users_collection.find_one({"email": email}):
            flash("An account with this email already exists. Log in instead or use Forgot password.", "error")
            return render_template("register.html", email=email)

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        users_collection.insert_one({
            "email": email,
            "password": hashed,
            "auth_provider": "local"
        })

        flash("Registration successful. You can log in now.", "success")
        return redirect("/")

    return render_template("register.html", email="")
