from flask import Blueprint, render_template, request, redirect, session
from database.mongo import users_collection
from flask_bcrypt import Bcrypt

login_bp = Blueprint("login", __name__)

bcrypt = Bcrypt()


@login_bp.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = users_collection.find_one({"email": email})

        if user and bcrypt.check_password_hash(user["password"], password):

            session["user"] = email
            return redirect("/dashboard")

    return render_template("login.html")