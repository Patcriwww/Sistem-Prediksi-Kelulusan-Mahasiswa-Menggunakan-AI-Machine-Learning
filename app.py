import os
import logging
import pandas as pd
from flask import (
    Flask, render_template, request,
    redirect, url_for, session
)
from joblib import load

# =========================================================
# KONFIGURASI LOGGING
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# =========================================================
# APP
# =========================================================
app = Flask(__name__)
app.secret_key = "araas-secret-key"  # ganti di production

# =========================================================
# GLOBAL SECURITY GUARD (LOGIN WAJIB) — FIXED
# =========================================================
@app.before_request
def require_login():
    # FIX WAJIB: cegah endpoint None (favicon, refresh, back)
    if request.endpoint is None:
        return

    allowed = {"login", "static"}
    if request.endpoint not in allowed:
        if "role" not in session:
            return redirect(url_for("login"))

# =========================================================
# DUMMY USERS (LOGIN ROLE)
# =========================================================
USERS = {
    "mahasiswa1": {"password": "12345", "role": "mahasiswa"},
    "akademik1": {"password": "admin123", "role": "akademik"},
}

# =========================================================
# LOAD MODEL
# =========================================================
MODEL_PATH = "model_kelulusan.joblib"
model = None
model_load_error = None

if os.path.exists(MODEL_PATH):
    try:
        model = load(MODEL_PATH)
        logger.info("Model berhasil dimuat dari %s", MODEL_PATH)
    except Exception as e:
        model_load_error = f"Gagal load model: {e}"
        logger.exception(model_load_error)
else:
    model_load_error = f"Model file tidak ditemukan di '{MODEL_PATH}'"
    logger.error(model_load_error)

# =========================================================
# HELPER VALIDASI
# =========================================================
def to_float(value, name):
    try:
        return float(value)
    except Exception:
        raise ValueError(f"Field '{name}' harus berupa angka.")

def to_int(value, name):
    try:
        return int(float(value))
    except Exception:
        raise ValueError(f"Field '{name}' harus berupa bilangan bulat.")

# =========================================================
# SOFTBOOST
# =========================================================
def adjust_prob_softboost(prob, row):
    boost = 0.0
    if row["ipk"] >= 3.9:
        boost += 0.12
    elif row["ipk"] >= 3.7:
        boost += 0.07

    if row["presensi"] >= 98:
        boost += 0.10
    elif row["presensi"] >= 95:
        boost += 0.05

    if row["mengulang"] == 0:
        boost += 0.05

    if row["sks_lulus"] >= 140:
        boost += 0.03

    return min(prob + boost, 0.985)

# =========================================================
# PREDIKSI
# =========================================================
def prediksi_kelulusan(ipk, sks_lulus, presensi, mengulang):
    if model is None:
        raise RuntimeError(model_load_error or "Model tidak tersedia")

    df = pd.DataFrame([{
        "ipk": ipk,
        "sks_lulus": sks_lulus,
        "presensi": presensi,
        "mengulang": mengulang
    }])

    y_pred = model.predict(df)[0]

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(df)[0]
        classes = list(getattr(model, "classes_", []))
        idx = classes.index(1) if 1 in classes else 1
        prob = float(probs[idx])
    else:
        prob = float(bool(y_pred))

    prob = adjust_prob_softboost(prob, df.iloc[0])
    prob_percent = prob * 100

    label = "Lulus tepat waktu" if y_pred == 1 else "Berisiko terlambat"

    if prob_percent >= 85:
        rekomendasi = "Pertahankan performa akademik."
    elif prob_percent >= 60:
        rekomendasi = "Perlu konseling akademik dan peningkatan presensi."
    else:
        rekomendasi = "Wajib mentoring intensif dan evaluasi studi."

    return label, prob_percent, rekomendasi

# =========================================================
# ROOT → LOGIN
# =========================================================
@app.route("/")
def root():
    return redirect(url_for("login"))

# =========================================================
# LOGIN
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = USERS.get(username)
        if not user or user["password"] != password:
            error = "Username atau password salah"
        else:
            session["username"] = username
            session["role"] = user["role"]
            logger.info("Login sukses: %s (%s)", username, user["role"])

            if user["role"] == "mahasiswa":
                return redirect(url_for("mahasiswa"))
            return redirect(url_for("akademik"))

    return render_template("login.html", error=error)

# =========================================================
# LOGOUT
# =========================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================================================
# MAHASISWA
# =========================================================
@app.route("/mahasiswa", methods=["GET", "POST"])
def mahasiswa():
    if session.get("role") != "mahasiswa":
        return redirect(url_for("login"))

    result, error = None, model_load_error

    if request.method == "POST":
        try:
            nama = request.form.get("nama", "").strip()
            nim = request.form.get("nim", "").strip()

            ipk = to_float(request.form.get("ipk"), "ipk")
            sks = to_int(request.form.get("sks_lulus"), "sks_lulus")
            presensi = to_int(request.form.get("presensi"), "presensi")
            mengulang = to_int(request.form.get("mengulang"), "mengulang")

            label, prob, rekomendasi = prediksi_kelulusan(
                ipk, sks, presensi, mengulang
            )

            result = {
                "nama": nama,
                "nim": nim,
                "label": label,
                "probabilitas": f"{prob:.2f}%",
                "prob_value": prob,
                "rekomendasi": rekomendasi,
            }

        except Exception as e:
            error = str(e)

    return render_template("index.html", result=result, error=error)

# =========================================================
# AKADEMIK (ARaaS)
# =========================================================
@app.route("/akademik", methods=["GET", "POST"])
def akademik():
    if session.get("role") != "akademik":
        return redirect(url_for("login"))

    results, summary, error = [], [], None

    if request.method == "POST":
        file = request.files.get("file")

        if not file or not file.filename.endswith(".csv"):
            error = "File CSV tidak valid"
        else:
            df = pd.read_csv(file)

            for _, row in df.iterrows():
                label, prob, _ = prediksi_kelulusan(
                    row["ipk"],
                    row["sks_lulus"],
                    row["presensi"],
                    row["mengulang"]
                )

                results.append({
                    "nama": row["nama"],
                    "nim": row["nim"],
                    "angkatan": row["angkatan"],
                    "label": label,
                    "probabilitas": prob,
                })

            summary = (
                pd.DataFrame(results)
                .groupby("angkatan")
                .size()
                .reset_index(name="total")
                .to_dict(orient="records")
            )

    return render_template("upload.html", results=results, summary=summary, error=error)

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    debug_flag = os.getenv("FLASK_DEBUG", "True").lower() in ("1", "true", "yes")
    app.run(debug=debug_flag)
