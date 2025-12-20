from flask import Blueprint, render_template, request, redirect, url_for, session
from services.auth_service import get_student_profile_by_username
from services.prediction_service import predict_for_user
from models.prediction_repository import save_prediction, load_predictions

mahasiswa_bp = Blueprint("mahasiswa", __name__, url_prefix="/dashboard/mahasiswa")


@mahasiswa_bp.route("/", endpoint="dashboard")
def dashboard():
    if session.get("role") != "mahasiswa":
        return redirect(url_for("auth.login"))

    username = (session.get("user") or "").strip()
    profile = get_student_profile_by_username(username)

    # Riwayat hanya milik mahasiswa login
    all_rows = load_predictions()
    history = [r for r in all_rows if str(r.get("username", "")).strip() == username]
    history = sorted(history, key=lambda x: str(x.get("timestamp","")))

    return render_template("dashboard_mahasiswa.html", profile=profile, history=history)


@mahasiswa_bp.route("/predict", methods=["POST"], endpoint="predict")
def predict():
    if session.get("role") != "mahasiswa":
        return redirect(url_for("auth.login"))

    username = (session.get("user") or "").strip()

    result = predict_for_user(
        username=username,
        ipk=request.form.get("ipk", 0),
        mengulang=request.form.get("mengulang", 0),
        presensi=request.form.get("presensi", 0),
        sks_lulus=request.form.get("sks_lulus", 0),
    )

    save_prediction(result)
    session["result"] = result
    return redirect(url_for("mahasiswa.dashboard"))
