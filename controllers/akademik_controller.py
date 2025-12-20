from flask import Blueprint, render_template, redirect, url_for, session, send_file, request, jsonify
import os

from models.prediction_repository import (
    load_predictions,
    delete_all_predictions,
    delete_predictions_by_nim,
    delete_prediction_by_id,
)

from services.report_service import export_excel, export_pdf
from services.auth_service import create_user, get_user_by_username
from models.db_models import User, Student
from extensions import db

akademik_bp = Blueprint("akademik", __name__, url_prefix="/dashboard/akademik")


# ----------------------------
# List pages for akademik
# ----------------------------
@akademik_bp.route('/dosen', endpoint='dosen_list')
def dosen_list():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    dosens = User.query.filter_by(role='dosen').order_by(User.username).all()
    return render_template('dosen_list.html', dosens=dosens)


@akademik_bp.route('/dosen/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_dosen(user_id):
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    u = User.query.get_or_404(user_id)
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        if not username:
            return render_template('edit_dosen.html', user=u, error='Username wajib')

        # username unique check
        existing = User.query.filter(User.username==username, User.id!=u.id).first()
        if existing:
            return render_template('edit_dosen.html', user=u, error='Username sudah digunakan oleh user lain')

        u.username = username
        if password:
            u.password_hash = create_user(username=username, password=password, role=u.role).password_hash
            # create_user created a new user; fix by fetching the hashed password and deleting the new extra user
            extra = User.query.filter(User.username==username, User.id!=u.id).first()
            if extra:
                # copy hashed pw from extra then remove extra row
                u.password_hash = extra.password_hash
                db.session.delete(extra)

        db.session.commit()
        return render_template('edit_dosen.html', user=u, success=True)

    return render_template('edit_dosen.html', user=u)


@akademik_bp.route('/dosen/<int:user_id>/delete', methods=['POST'], endpoint='delete_dosen')
def delete_dosen(user_id):
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    u = User.query.get_or_404(user_id)
    if u.role == 'dosen':
        db.session.delete(u)
        db.session.commit()
    return redirect(url_for('akademik.dosen_list'))


@akademik_bp.route('/mahasiswa', endpoint='mahasiswa_list')
def mahasiswa_list():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    students = Student.query.order_by(Student.nim).all()
    return render_template('mahasiswa_list.html', students=students)


@akademik_bp.route('/mahasiswa/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_mahasiswa(student_id):
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    s = Student.query.get_or_404(student_id)
    dosen_list = User.query.filter_by(role='dosen').all()
    from models.db_models import Kelas
    kelas_list = Kelas.query.order_by(Kelas.code).all()

    if request.method == 'POST':
        nama = (request.form.get('nama_mahasiswa') or '').strip()
        nim = (request.form.get('nim') or '').strip()
        prodi = (request.form.get('prodi') or '').strip()
        angkatan = (request.form.get('angkatan') or '').strip()
        kelas_code = request.form.get('kelas_code')
        advisor_username = (request.form.get('advisor_username') or '').strip()

        if not nama or not nim:
            return render_template('edit_mahasiswa.html', student=s, dosen_list=dosen_list, kelas_list=kelas_list, error='Nama dan NIM wajib')

        # check nim uniqueness
        existing = Student.query.filter(Student.nim==nim, Student.id!=s.id).first()
        if existing:
            return render_template('edit_mahasiswa.html', student=s, dosen_list=dosen_list, kelas_list=kelas_list, error='NIM sudah digunakan')

        s.nama_mahasiswa = nama
        s.nim = nim
        s.prodi = prodi
        s.angkatan = angkatan

        # assign kelas_code if provided
        if kelas_code:
            try:
              s.kelas_code = request.form.get("kelas_code")
            except ValueError:
                s.kelas_code = None

        advisor = get_user_by_username(advisor_username) if advisor_username else None
        s.advisor_id = advisor.id if advisor and advisor.role == 'dosen' else None

        db.session.commit()
        return render_template('edit_mahasiswa.html', student=s, dosen_list=dosen_list, kelas_list=kelas_list, success=True)

    return render_template('edit_mahasiswa.html', student=s, dosen_list=dosen_list, kelas_list=kelas_list)


@akademik_bp.route('/mahasiswa/<int:student_id>/delete', methods=['POST'], endpoint='delete_mahasiswa')
def delete_mahasiswa(student_id):
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    s = Student.query.get_or_404(student_id)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for('akademik.mahasiswa_list'))



@akademik_bp.route("/", endpoint="dashboard")
def dashboard():
    if session.get("role") != "akademik":
        return redirect(url_for("auth.login"))

    data = load_predictions()
    # sort newest first
    data = sorted(data, key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return render_template("dashboard_akademik.html", data=data)


@akademik_bp.route('/dosen/add', methods=['GET', 'POST'])
def add_dosen():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        if not username or not password:
            return render_template('add_dosen.html', error='Username dan password wajib.')

        if get_user_by_username(username):
            return render_template('add_dosen.html', error='Username sudah ada.')

        create_user(username=username, password=password, role='dosen')
        return render_template('add_dosen.html', success=True)

    return render_template('add_dosen.html')


@akademik_bp.route('/mahasiswa/add', methods=['GET', 'POST'])
def add_mahasiswa():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    dosen_list = User.query.filter_by(role='dosen').all()
    from models.db_models import Kelas
    kelas_list = Kelas.query.order_by(Kelas.code).all()

    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        nama = (request.form.get('nama_mahasiswa') or '').strip()
        nim = (request.form.get('nim') or '').strip()
        prodi = (request.form.get('prodi') or '').strip()
        angkatan = (request.form.get('angkatan') or '').strip()
        kelas_code = (request.form.get('kelas_code') or '').strip()
        advisor_username = (request.form.get('advisor_username') or '').strip()

        if not nama or not nim:
            return render_template('add_mahasiswa.html', dosen_list=dosen_list, kelas_list=kelas_list, error='Nama dan NIM wajib.')

        if Student.query.filter_by(nim=nim).first():
            return render_template('add_mahasiswa.html', dosen_list=dosen_list, kelas_list=kelas_list, error='NIM sudah ada.')

        user_id = None
        if username:
            existing = get_user_by_username(username)
            if existing:
                return render_template('add_mahasiswa.html', dosen_list=dosen_list, kelas_list=kelas_list, error='Username sudah ada.')
            if not password:
                return render_template('add_mahasiswa.html', dosen_list=dosen_list, kelas_list=kelas_list, error='Password wajib jika membuat user.')
            u = create_user(username=username, password=password, role='mahasiswa')
            user_id = u.id

        advisor = get_user_by_username(advisor_username) if advisor_username else None
        advisor_id = advisor.id if advisor and advisor.role == 'dosen' else None

        kelas_code_val = None
        if kelas_code:
            try:
                kelas_code_val = int(kelas_code)
            except ValueError:
                kelas_code_val = None

        s = Student(user_id=user_id, nama_mahasiswa=nama, nim=nim, prodi=prodi, angkatan=angkatan, kelas_code=kelas_code_val, advisor_id=advisor_id)
        db.session.add(s)
        db.session.commit()

        return render_template('add_mahasiswa.html', dosen_list=dosen_list, kelas_list=kelas_list, success=True)

    return render_template('add_mahasiswa.html', dosen_list=dosen_list, kelas_list=kelas_list)


@akademik_bp.route('/mahasiswa/assign-advisor', methods=['GET', 'POST'])
def assign_advisor():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))

    dosen_list = User.query.filter_by(role='dosen').all()
    students = Student.query.all()

    if request.method == 'POST':
        nim = (request.form.get('nim') or '').strip()
        advisor_username = (request.form.get('advisor_username') or '').strip()

        s = Student.query.filter_by(nim=nim).first()
        advisor = get_user_by_username(advisor_username)

        if not s:
            return render_template('assign_advisor.html', students=students, dosen_list=dosen_list, error='Mahasiswa tidak ditemukan.')
        if not advisor or advisor.role != 'dosen':
            return render_template('assign_advisor.html', students=students, dosen_list=dosen_list, error='Dosen tidak ditemukan.')

        s.advisor_id = advisor.id
        db.session.commit()
        return render_template('assign_advisor.html', students=students, dosen_list=dosen_list, success=True)

    return render_template('assign_advisor.html', students=students, dosen_list=dosen_list)


@akademik_bp.route("/api/risk-summary", endpoint="risk_summary")
def risk_summary():
    if session.get("role") != "akademik":
        return jsonify({"labels": [], "values": []})

    rows = load_predictions()
    low = sum(1 for r in rows if r.get("risk") == "Low Risk")
    med = sum(1 for r in rows if r.get("risk") == "Medium Risk")
    high = sum(1 for r in rows if r.get("risk") == "High Risk")

    labels = ["Low Risk", "Medium Risk", "High Risk"]
    values = [low, med, high]
    return jsonify({"labels": labels, "values": values})


# ----------------------------
# Fakultas (CRUD for akademik)
# ----------------------------
@akademik_bp.route('/fakultas', endpoint='fakultas_list')
def fakultas_list():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))
    from models.db_models import Fakultas
    fakultas_list = Fakultas.query.order_by(Fakultas.code).all()
    return render_template('fakultas_list.html', fakultas_list=fakultas_list)


@akademik_bp.route('/fakultas/add', methods=['GET', 'POST'])
def add_fakultas():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))
    from models.db_models import Fakultas

    if request.method == 'POST':
        code = (request.form.get('code') or '').strip()
        name = (request.form.get('name') or '').strip()
        if not code:
            return render_template('add_fakultas.html', error='Kode fakultas wajib')
        if Fakultas.query.filter_by(code=code).first():
            return render_template('add_fakultas.html', error='Kode sudah ada')
        f = Fakultas(code=code, name=name)
        db.session.add(f)
        db.session.commit()
        return render_template('add_fakultas.html', success=True)

    return render_template('add_fakultas.html')


@akademik_bp.route('/fakultas/<int:fakultas_id>/edit', methods=['GET', 'POST'])
def edit_fakultas(fakultas_id):
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))
    from models.db_models import Fakultas
    f = Fakultas.query.get_or_404(fakultas_id)
    if request.method == 'POST':
        code = (request.form.get('code') or '').strip()
        name = (request.form.get('name') or '').strip()
        if not code:
            return render_template('edit_fakultas.html', fakultas=f, error='Kode wajib')
        existing = Fakultas.query.filter(Fakultas.code==code, Fakultas.id!=f.id).first()
        if existing:
            return render_template('edit_fakultas.html', fakultas=f, error='Kode sudah digunakan')
        f.code = code
        f.name = name
        db.session.commit()
        return render_template('edit_fakultas.html', fakultas=f, success=True)
    return render_template('edit_fakultas.html', fakultas=f)


@akademik_bp.route('/fakultas/<int:fakultas_id>/delete', methods=['POST'], endpoint='delete_fakultas')
def delete_fakultas(fakultas_id):
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))
    from models.db_models import Fakultas
    f = Fakultas.query.get_or_404(fakultas_id)
    db.session.delete(f)
    db.session.commit()
    return redirect(url_for('akademik.fakultas_list'))


# ----------------------------
# Kelas (CRUD for akademik)
# ----------------------------
@akademik_bp.route('/kelas', endpoint='kelas_list')
def kelas_list():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))
    from models.db_models import Kelas
    kelas_list = Kelas.query.order_by(Kelas.code).all()
    return render_template('kelas_list.html', kelas_list=kelas_list)


@akademik_bp.route('/kelas/add', methods=['GET', 'POST'])
def add_kelas():
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))
    from models.db_models import Kelas, Fakultas
    fakultas_list = Fakultas.query.order_by(Fakultas.code).all()

    if request.method == 'POST':
        code = (request.form.get('code') or '').strip()
        name = (request.form.get('name') or '').strip()
        fakultas_id = (request.form.get('fakultas_id') or '').strip()
        if not code:
            return render_template('add_kelas.html', fakultas_list=fakultas_list, error='Kode kelas wajib')
        if Kelas.query.filter_by(code=code).first():
            return render_template('add_kelas.html', fakultas_list=fakultas_list, error='Kode sudah ada')
        f_id = None
        if fakultas_id:
            try:
                f_id = int(fakultas_id)
            except ValueError:
                f_id = None
        k = Kelas(code=code, name=name, fakultas_id=f_id)
        db.session.add(k)
        db.session.commit()
        return render_template('add_kelas.html', fakultas_list=fakultas_list, success=True)

    return render_template('add_kelas.html', fakultas_list=fakultas_list)


@akademik_bp.route('/kelas/<int:kelas_code>/edit', methods=['GET', 'POST'])
def edit_kelas(kelas_code):
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))
    from models.db_models import Kelas, Fakultas
    k = Kelas.query.get_or_404(kelas_code)
    fakultas_list = Fakultas.query.order_by(Fakultas.code).all()
    if request.method == 'POST':
        code = (request.form.get('code') or '').strip()
        name = (request.form.get('name') or '').strip()
        fakultas_id = (request.form.get('fakultas_id') or '').strip()
        if not code:
            return render_template('edit_kelas.html', kelas=k, fakultas_list=fakultas_list, error='Kode wajib')
        existing = Kelas.query.filter(Kelas.code==code, Kelas.code!=k.id).first()
        if existing:
            return render_template('edit_kelas.html', kelas=k, fakultas_list=fakultas_list, error='Kode sudah digunakan')
        k.code = code
        k.name = name
        try:
            k.fakultas_id = int(fakultas_id) if fakultas_id else None
        except ValueError:
            k.fakultas_id = None
        db.session.commit()
        return render_template('edit_kelas.html', kelas=k, fakultas_list=fakultas_list, success=True)
    return render_template('edit_kelas.html', kelas=k, fakultas_list=fakultas_list)


@akademik_bp.route('/kelas/<int:kelas_code>/delete', methods=['POST'], endpoint='delete_kelas')
def delete_kelas(kelas_code):
    if session.get('role') != 'akademik':
        return redirect(url_for('auth.login'))
    from models.db_models import Kelas
    k = Kelas.query.get_or_404(kelas_code)
    db.session.delete(k)
    db.session.commit()
    return redirect(url_for('akademik.kelas_list'))


@akademik_bp.route("/mahasiswa/<nim>", endpoint="detail_mahasiswa")
def detail_mahasiswa(nim):
    if session.get("role") not in ["akademik"]:
        return redirect(url_for("auth.login"))

    nim = str(nim).strip().replace(".0", "")
    rows = load_predictions()

    history = []
    for r in rows:
        rn = str(r.get("nim", "")).strip().replace(".0", "")
        if rn == nim:
            history.append(r)

    if not history:
        return "Data mahasiswa tidak ditemukan", 404

    history = sorted(history, key=lambda x: str(x.get("timestamp", "")))
    profile = history[0]

    # try to find student in DB to show advisor info
    student = Student.query.filter_by(nim=profile.get('nim')).first()
    advisor = None
    if student and student.advisor_id:
        advisor = User.query.get(student.advisor_id)

    return render_template("detail_mahasiswa.html", profile=profile, history=history, back_url=url_for("akademik.dashboard"), advisor=advisor)


@akademik_bp.route("/export/excel", endpoint="export_excel_route")
def export_excel_route():
    if session.get("role") != "akademik":
        return redirect(url_for("auth.login"))

    os.makedirs("reports", exist_ok=True)
    path = "reports/laporan.xlsx"
    rows = load_predictions()
    export_excel(rows, path)
    return send_file(path, as_attachment=True)


@akademik_bp.route("/export/pdf", endpoint="export_pdf_route")
def export_pdf_route():
    if session.get("role") != "akademik":
        return redirect(url_for("auth.login"))

    os.makedirs("reports", exist_ok=True)
    path = "reports/laporan.pdf"
    rows = load_predictions()
    export_pdf(rows, path)
    return send_file(path, as_attachment=True)


@akademik_bp.route("/delete/all", methods=["POST"], endpoint="delete_all")
def delete_all():
    if session.get("role") != "akademik":
        return redirect(url_for("auth.login"))

    delete_all_predictions()
    return redirect(url_for("akademik.dashboard"))


@akademik_bp.route("/delete/nim/<nim>", methods=["POST"], endpoint="delete_by_nim")
def delete_by_nim(nim):
    if session.get("role") != "akademik":
        return redirect(url_for("auth.login"))

    delete_predictions_by_nim(nim)
    return redirect(url_for("akademik.dashboard"))


@akademik_bp.route("/delete/one", methods=["POST"], endpoint="delete_one")
def delete_one():
    if session.get("role") != "akademik":
        return redirect(url_for("auth.login"))

    record_id = (request.form.get("record_id") or "").strip()
    if record_id:
        delete_prediction_by_id(record_id)

    return redirect(url_for("akademik.dashboard"))
