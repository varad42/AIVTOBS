import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_bcrypt import Bcrypt

from config import PASSWORD_RESET_HOURS
from database.mongo import users_collection
from auth.utils import normalize_email, validate_password


password_reset_bp = Blueprint("password_reset", __name__)

bcrypt = Bcrypt()


@password_reset_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    reset_link = None

    if request.method == "POST":
        email = normalize_email(request.form.get("email"))

        if not email:
            flash("Enter your email address so we can help you reset your password.", "error")
            return render_template("forgot_password.html", reset_link=reset_link)

        user = users_collection.find_one({"email": email})

        if not user:
            flash("We could not find an account for that email. Try registering first or check for typing mistakes.", "error")
            return render_template("forgot_password.html", reset_link=reset_link)

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_HOURS)

        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_token": token,
                    "reset_token_expires_at": expires_at
                }
            }
        )

        reset_link = url_for("password_reset.reset_password", token=token, _external=True)
        flash("Password reset link created. Open the link below to set a new password.", "success")

    return render_template("forgot_password.html", reset_link=reset_link)


@password_reset_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    now = datetime.now(timezone.utc)
    user = users_collection.find_one(
        {
            "reset_token": token,
            "reset_token_expires_at": {"$gt": now}
        }
    )

    if not user:
        flash("This reset link is invalid or has expired. Request a new one and try again.", "error")
        return redirect(url_for("password_reset.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        password_error = validate_password(password)

        if password_error:
            flash(f"{password_error} Try a longer password and submit again.", "error")
            return render_template("reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords did not match. Re-enter the same new password in both fields.", "error")
            return render_template("reset_password.html", token=token)

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password": hashed},
                "$unset": {
                    "reset_token": "",
                    "reset_token_expires_at": ""
                }
            }
        )

        flash("Password updated successfully. You can now log in with your new password.", "success")
        return redirect(url_for("login.login"))

    return render_template("reset_password.html", token=token)
