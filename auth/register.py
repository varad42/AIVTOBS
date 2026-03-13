from flask import Blueprint, render_template, request, redirect, session
from database.mongo import users_collection
from flask_bcrypt import Bcrypt

register_bp = Blueprint("register", __name__)

bcrypt = Bcrypt()


@register_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        users_collection.insert_one({
            "email": email,
            "password": hashed
        })

        return redirect("/")

    return render_template("register.html")