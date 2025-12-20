from flask import Blueprint, render_template, request, redirect, url_for, session
from services.auth_service import get_user_by_username, check_pw

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")

        user = get_user_by_username(u)
        if user and check_pw(p, user.password_hash):
            session["user"] = u
            session["role"] = user.role
            return redirect(url_for(f"{user.role}.dashboard"))

        return render_template("login.html", error="Login gagal. Periksa username/password.")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        return render_template("forgot_password.html", success=True)
    return render_template("forgot_password.html", success=False)
