import joblib
import pandas as pd
from datetime import datetime
import uuid

from services.auth_service import get_student_profile_by_username

MODEL_PATH = "model_kelulusan.joblib"
model = joblib.load(MODEL_PATH)

FEATURE_ORDER = list(getattr(model, "feature_names_in_", ["ipk", "mengulang", "presensi", "sks_lulus"]))

def classify_risk(prob: float) -> str:
    if prob >= 0.85:
        return "Low Risk"
    elif prob >= 0.60:
        return "Medium Risk"
    return "High Risk"

def recommendation(risk: str) -> str:
    return {
        "Low Risk": "Pertahankan performa akademik dan tingkatkan konsistensi belajar.",
        "Medium Risk": "Disarankan bimbingan akademik rutin dan evaluasi strategi belajar.",
        "High Risk": "Perlu intervensi: konseling, pendampingan intensif, dan monitoring berkala."
    }[risk]

def predict_for_user(username: str, ipk: float, mengulang: int, presensi: int, sks_lulus: int) -> dict:
    profile = get_student_profile_by_username(username)
    if not profile:
        raise ValueError("Profil mahasiswa tidak ditemukan.")

    raw_input = {
        "ipk": float(ipk),
        "mengulang": int(mengulang),
        "presensi": int(presensi),
        "sks_lulus": int(sks_lulus),
    }

    X = pd.DataFrame([[raw_input[f] for f in FEATURE_ORDER]], columns=FEATURE_ORDER)
    prob = float(model.predict_proba(X)[0][1])

    risk = classify_risk(prob)
    rec = recommendation(risk)

    return {
        "record_id": str(uuid.uuid4()),
        "username": username,
        "nama_mahasiswa": profile.get("nama_mahasiswa", ""),
        "nim": profile.get("nim", ""),
        "prodi": profile.get("prodi", ""),
        "angkatan": profile.get("angkatan", ""),
        "kelas": profile.get("kelas", ""),

        "ipk": str(raw_input["ipk"]),
        "mengulang": str(raw_input["mengulang"]),
        "presensi": str(raw_input["presensi"]),
        "sks_lulus": str(raw_input["sks_lulus"]),

        "probability": str(round(prob * 100, 2)),
        "risk": risk,
        "recommendation": rec,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
