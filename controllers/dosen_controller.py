from flask import Blueprint, render_template, redirect, url_for, session, request
from services.auth_service import get_user_by_username
from models.db_models import ClassModel, Student, User, Kelas, Fakultas
from models.prediction_repository import load_predictions

dosen_bp = Blueprint("dosen", __name__, url_prefix="/dashboard/dosen")


@dosen_bp.route("/", endpoint="dashboard")
def dashboard():
    # ======================
    # AUTH CHECK
    # ======================
    if session.get("role") != "dosen":
        return redirect(url_for("auth.login"))

    dosen = get_user_by_username(session.get("user"))
    if not dosen:
        return redirect(url_for("auth.login"))

    # ======================
    # KELAS YANG DIAJAR DOSEN
    # ======================
    my_classes = (
        ClassModel.query
        .filter(ClassModel.dosen_id == dosen.id)
        .all()
    )

    class_codes = [c.code for c in my_classes]

    if not class_codes:
        return render_template(
            "dashboard_dosen.html",
            data=[],
            fakultas_list=[],
            kelas_list=[],
            summary=_empty_summary(),
            selected_fakultas="",
            selected_kelas="",
        )

    # ======================
    # MASTER KELAS (FILTER UI)
    # ======================
    kelas_list = (
        Kelas.query
        .filter(Kelas.code.in_(class_codes))
        .order_by(Kelas.code)
        .all()
    )

    # ======================
    # MASTER FAKULTAS (FIX FINAL)
    # ======================
    fakultas_list = (
        Fakultas.query
        .join(Kelas, Kelas.fakultas_id == Fakultas.id)
        .filter(Kelas.code.in_(class_codes))
        .distinct()
        .order_by(Fakultas.code)
        .all()
    )

    # ======================
    # FILTER DARI UI
    # ======================
    selected_fakultas = request.args.get("fakultas", "").strip()
    selected_kelas = request.args.get("kelas", "").strip()

    # ======================
    # QUERY MAHASISWA
    # ======================
    students_q = (
        Student.query
        .join(User, User.id == Student.user_id)
        .filter(Student.kelas_code.in_(class_codes))
    )

    if selected_kelas:
        students_q = students_q.filter(
            Student.kelas_code == selected_kelas
        )

    if selected_fakultas:
        students_q = (
            students_q
            .join(Kelas, Student.kelas_code == Kelas.code)
            .filter(Kelas.fakultas_id == int(selected_fakultas))
        )

    students = students_q.all()

    # ======================
    # AMBIL NIM
    # ======================
    nims = {
        str(s.nim).strip().replace(".0", "")
        for s in students
        if s.nim
    }

    # ======================
    # LOAD & FILTER PREDIKSI
    # ======================
    rows = [
        r for r in load_predictions()
        if str(r.get("nim", "")).strip().replace(".0", "") in nims
    ]

    # ======================
    # SUMMARY
    # ======================
    summary = _build_summary(rows)

    # ======================
    # SORT TERBARU
    # ======================
    rows = sorted(
        rows,
        key=lambda x: str(x.get("timestamp", "")),
        reverse=True
    )

    return render_template(
        "dashboard_dosen.html",
        data=rows,
        fakultas_list=fakultas_list,
        kelas_list=kelas_list,
        summary=summary,
        selected_fakultas=selected_fakultas,
        selected_kelas=selected_kelas,
    )


# ======================
# HELPER FUNCTIONS
# ======================
def _empty_summary():
    return {
        "total": 0,
        "low": 0, "low_pct": 0,
        "med": 0, "med_pct": 0,
        "high": 0, "high_pct": 0,
    }


def _build_summary(rows):
    total = len(rows)
    low = sum(1 for r in rows if r.get("risk") == "Low Risk")
    med = sum(1 for r in rows if r.get("risk") == "Medium Risk")
    high = sum(1 for r in rows if r.get("risk") == "High Risk")

    def pct(x):
        return round((x / total) * 100, 1) if total else 0

    return {
        "total": total,
        "low": low, "low_pct": pct(low),
        "med": med, "med_pct": pct(med),
        "high": high, "high_pct": pct(high),
    }
