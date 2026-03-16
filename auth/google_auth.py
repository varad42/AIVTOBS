import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests
from flask import Blueprint, flash, redirect, request, session, url_for

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from database.mongo import users_collection
from auth.utils import normalize_email


google_auth_bp = Blueprint("google_auth", __name__)


def google_configured():

    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


@google_auth_bp.route("/auth/google")
def google_login():

    if not google_configured():
        flash("Google login is not configured yet. Add Google client credentials in the environment settings first.", "error")
        return redirect(url_for("login.login"))

    state = secrets.token_urlsafe(24)
    session["google_oauth_state"] = state

    query = urlencode(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": url_for("google_auth.google_callback", _external=True),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account"
        }
    )

    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@google_auth_bp.route("/auth/google/callback")
def google_callback():

    if request.args.get("state") != session.pop("google_oauth_state", None):
        flash("Google login could not be verified. Please click the Google button again.", "error")
        return redirect(url_for("login.login"))

    code = request.args.get("code")

    if not code:
        flash("Google login was cancelled or did not return an authorization code.", "error")
        return redirect(url_for("login.login"))

    try:
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": url_for("google_auth.google_callback", _external=True),
                "grant_type": "authorization_code"
            },
            timeout=15
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        access_token = token_data.get("access_token")

        if not access_token:
            flash("Google login did not return an access token. Please try again.", "error")
            return redirect(url_for("login.login"))

        profile_response = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15
        )
        profile_response.raise_for_status()
        profile = profile_response.json()
    except requests.RequestException:
        flash("Google login failed while contacting Google. Please try again in a moment.", "error")
        return redirect(url_for("login.login"))

    email = normalize_email(profile.get("email"))
    google_sub = profile.get("sub")

    if not email:
        flash("Google login succeeded but did not return an email address for this account.", "error")
        return redirect(url_for("login.login"))

    users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "google_sub": google_sub,
                "auth_provider": "google",
                "last_login_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

    session["user"] = email
    flash("Logged in with Google successfully.", "success")
    return redirect(url_for("dashboard"))
