"""Seed script: create tables and insert initial users & students."""
from app import create_app, db
from models.db_models import User, Student, ClassModel, ClassStudent
from services.auth_service import create_user
import bcrypt

app = create_app()

def hash_pw_str(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode()

with app.app_context():
    print("Creating tables...")
    db.create_all()

    # Ensure advisor column exists (for existing DBs) and set DB structure before any Student queries
    try:
        rc = db.engine.raw_connection()
        cur = rc.cursor()
        cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS advisor_id INT;")
        # create index (safe)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_students_advisor ON students(advisor_id);")
        rc.commit()
        cur.close()
        rc.close()
    except Exception:
        # if raw_connection not available or fails, fall back to engine.execute
        try:
            with db.engine.connect() as conn:
                conn.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS advisor_id INT;")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_students_advisor ON students(advisor_id);")
        except Exception:
            pass

    # Create users
    users = [
        ("mhs01", "mahasiswa"),
        ("mhs02", "mahasiswa"),
        ("mhs03", "mahasiswa"),
        ("mhs04", "mahasiswa"),
        ("dosen01", "dosen"),
        ("admin01", "akademik"),
    ]

    for username, role in users:
        if not User.query.filter_by(username=username).first():
            u = User(username=username, password_hash=hash_pw_str("123"), role=role)
            db.session.add(u)

    db.session.commit()

    # Create students (link to users where possible)
    profiles = {
        "mhs01": {"nama_mahasiswa":"Alamsyah Hutama","nim":"0112523004","prodi":"Informatika","angkatan":"2023","kelas":"IF23"},
        "mhs02": {"nama_mahasiswa":"Bona Firmanto","nim":"0112523009","prodi":"Informatika","angkatan":"2023","kelas":"IF23"},
        "mhs03": {"nama_mahasiswa":"M. Ridwan","nim":"0112523022","prodi":"Informatika","angkatan":"2023","kelas":"IF23"},
        "mhs04": {"nama_mahasiswa":"Fachri Reyhan","nim":"0112523013","prodi":"Informatika","angkatan":"2023","kelas":"IF23"},
    }

    for username, p in profiles.items():
        if not Student.query.filter_by(nim=p["nim"]).first():
            user = User.query.filter_by(username=username).first()
            s = Student(
                user_id=user.id if user else None,
                nama_mahasiswa=p["nama_mahasiswa"],
                nim=p["nim"],
                prodi=p.get("prodi"),
                angkatan=p.get("angkatan"),
                kelas_code=p.get("kelas"),
            )
            db.session.add(s)

    db.session.commit()

    # Create class IF23 and link students
    if not ClassModel.query.filter_by(code="IF23").first():
        dosen = User.query.filter_by(username="dosen01").first()
        cls = ClassModel(code="IF23", name="Informatika 2023", dosen_id=dosen.id if dosen else None)
        db.session.add(cls)
        db.session.commit()

        students = Student.query.filter(Student.kelas_code=="IF23").all()
        for s in students:
            cs = ClassStudent(class_id=cls.id, student_id=s.id)
            db.session.add(cs)

        db.session.commit()

    # Ensure fakultas & kelas tables exist and map existing kelas codes to kelas rows
    try:
        rc = db.engine.raw_connection()
        cur = rc.cursor()
        sql = open('sql/alter_add_kelas_fakultas.sql', 'r', encoding='utf-8').read()
        cur.execute(sql)
        rc.commit()
        cur.close()
        rc.close()
    except Exception:
        # fall back to executing statements individually
        try:
            with db.engine.connect() as conn:
                sql = open('sql/alter_add_kelas_fakultas.sql', 'r', encoding='utf-8').read()
                for stmt in [s.strip() for s in sql.split(';') if s.strip()]:
                    try:
                        conn.execute(stmt)
                    except Exception:
                        pass
        except Exception:
            pass

    # seed sample fakultas and kelas
    from models.db_models import Fakultas, Kelas
    if not Fakultas.query.filter_by(code='FTI').first():
        f = Fakultas(code='FTI', name='Fakultas Teknik dan Ilmu Komputer')
        db.session.add(f)
        db.session.commit()

    fti = Fakultas.query.filter_by(code='FTI').first()
    if not Kelas.query.filter_by(code='IF23').first():
        k = Kelas(code='IF23', name='Informatika 2023', fakultas_id=fti.id if fti else None)
        db.session.add(k)
        db.session.commit()

    # map students with kelas_code to kelas_code
    try:
        k_if23 = Kelas.query.filter_by(code='IF23').first()
        if k_if23:
            students = Student.query.filter(Student.kelas_code=='IF23').all()
            for s in students:
                s.kelas_code = k_if23.id
            db.session.commit()
    except Exception:
        pass

    # Ensure advisor column exists (for existing DBs) and set sample advisors
    # Use raw SQL to add column and FK if not present
    try:
        with db.engine.connect() as conn:
            conn.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS advisor_id INT;")
            conn.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name WHERE tc.table_name = 'students' AND tc.constraint_type = 'FOREIGN KEY' AND kcu.column_name = 'advisor_id') THEN ALTER TABLE students ADD CONSTRAINT fk_students_advisor FOREIGN KEY (advisor_id) REFERENCES users(id) ON DELETE SET NULL; END IF; END$$;")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_students_advisor ON students(advisor_id);")
    except Exception:
        # some DB drivers may not like executing multiple DO blocks; skip gracefully
        pass

    # Ensure there is at least one more dosen (dosen02)
    if not User.query.filter_by(username="dosen02").first():
        create_user(username="dosen02", password="123", role="dosen")

    # Set sample advisor (dosen01) to mhs01
    dosen = User.query.filter_by(username="dosen01").first()
    mhs = Student.query.filter_by(nim="0112523004").first()
    if dosen and mhs:
        mhs.advisor_id = dosen.id
        db.session.commit()

    # --- Additional seeds: fakultas, kelas, classes and extra students ---
    from models.db_models import Fakultas, Kelas, ClassModel, ClassStudent

    # Ensure additional fakultas
    extra_fakultas = [
        ("FEB", "Fakultas Ekonomi dan Bisnis"),
        ("FISIP", "Fakultas Ilmu Sosial dan Ilmu Politik"),
    ]
    for code, name in extra_fakultas:
        if not Fakultas.query.filter_by(code=code).first():
            db.session.add(Fakultas(code=code, name=name))
    db.session.commit()

    # Ensure more kelas
    fti = Fakultas.query.filter_by(code='FTI').first()
    if not Kelas.query.filter_by(code='IF22').first():
        db.session.add(Kelas(code='IF22', name='Informatika 2022', fakultas_id=fti.id if fti else None))
    if not Kelas.query.filter_by(code='SI23').first():
        db.session.add(Kelas(code='SI23', name='Sistem Informasi 2023', fakultas_id=fti.id if fti else None))
    db.session.commit()

    # Ensure dosen02 exists and create ClassModel entries assigned to dosen02
    dosen02 = User.query.filter_by(username='dosen02').first()
    if not dosen02:
        create_user(username='dosen02', password='123', role='dosen')
        dosen02 = User.query.filter_by(username='dosen02').first()

    for code, name in [('IF22', 'Informatika 2022'), ('SI23', 'Sistem Informasi 2023')]:
        if not ClassModel.query.filter_by(code=code).first():
            cls = ClassModel(code=code, name=name, dosen_id=dosen02.id if dosen02 else None)
            db.session.add(cls)
    db.session.commit()

    # Add additional mahasiswa users and student profiles
    new_students = {
        'mhs05': {'nama_mahasiswa':'Siti Nur','nim':'0112523033','prodi':'Sistem Informasi','angkatan':'2023','kelas':'SI23'},
        'mhs06': {'nama_mahasiswa':'Ahmad Taufik','nim':'0112523044','prodi':'Informatika','angkatan':'2022','kelas':'IF22'},
    }
    for username, p in new_students.items():
        if not Student.query.filter_by(nim=p['nim']).first():
            user = User.query.filter_by(username=username).first()
            if not user:
                user = create_user(username=username, password='123', role='mahasiswa')
            kelas_obj = Kelas.query.filter_by(code=p['kelas']).first()
            s = Student(user_id=user.id if user else None, nama_mahasiswa=p['nama_mahasiswa'], nim=p['nim'], prodi=p['prodi'], angkatan=p['angkatan'], kelas_code=kelas_obj.id if kelas_obj else None)
            db.session.add(s)
    db.session.commit()

    # Link students to ClassModel via ClassStudent
    for code in ['IF22', 'SI23']:
        cls = ClassModel.query.filter_by(code=code).first()
        if cls:
            students = Student.query.filter((Student.kelas_code==code) | (Student.kelas.has(code=code))).all()
            for s in students:
                if not ClassStudent.query.filter_by(class_id=cls.id, student_id=s.id).first():
                    cs = ClassStudent(class_id=cls.id, student_id=s.id)
                    db.session.add(cs)
    db.session.commit()

    # Assign dosen02 as advisor to one of the new students
    mhs05 = Student.query.filter_by(nim='0112523033').first()
    if mhs05 and dosen02:
        mhs05.advisor_id = dosen02.id
        db.session.commit()

    print("Seeding completed.")
