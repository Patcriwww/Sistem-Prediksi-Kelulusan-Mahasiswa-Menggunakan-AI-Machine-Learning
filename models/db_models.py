from datetime import datetime
import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum("mahasiswa", "dosen", "akademik", name="user_roles"), nullable=False, default="mahasiswa")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    nama_mahasiswa = db.Column(db.String(255), nullable=False)
    nim = db.Column(db.String(50), unique=True, nullable=False)
    prodi = db.Column(db.String(100))
    angkatan = db.Column(db.String(10))
    # legacy free-text code (kept for backwards compatibility)
    kelas_code = db.Column(db.String(50))

    # new: FK to Kelas
    kelas_code = db.Column(db.Integer, db.ForeignKey("kelas.id", ondelete="SET NULL"), nullable=True)

    # new: advisor (dosen) mapping
    advisor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("student", uselist=False))
    advisor = db.relationship("User", foreign_keys=[advisor_id], backref=db.backref("advisees", lazy=True))
    kelas = db.relationship("Kelas", foreign_keys=[kelas_code], backref=db.backref("students", lazy=True))

    def __repr__(self):
        return f"<Student {self.nim} - {self.nama_mahasiswa}>"


class ClassModel(db.Model):
    __tablename__ = "classes"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255))
    dosen_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    dosen = db.relationship("User", backref=db.backref("classes", lazy=True))

    def __repr__(self):
        return f"<Class {self.code}>"


class Fakultas(db.Model):
    __tablename__ = "fakultas"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Fakultas {self.code} - {self.name}>"


class Kelas(db.Model):
    __tablename__ = "kelas"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255))
    fakultas_id = db.Column(db.Integer, db.ForeignKey("fakultas.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    fakultas = db.relationship("Fakultas", backref=db.backref("kelas", lazy=True))

    def __repr__(self):
        return f"<Kelas {self.code} - {self.name}>"


class ClassStudent(db.Model):
    __tablename__ = "class_students"
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (db.UniqueConstraint("class_id", "student_id", name="uniq_class_student"),)

    cls = db.relationship("ClassModel", backref=db.backref("class_students", cascade="all, delete-orphan"))
    student = db.relationship("Student", backref=db.backref("class_students", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ClassStudent class_id={self.class_id} student_id={self.student_id}>"


class Prediction(db.Model):
    __tablename__ = "predictions"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = db.Column(db.String(50))

    nama_mahasiswa = db.Column(db.String(255))
    nim = db.Column(db.String(50), index=True)
    prodi = db.Column(db.String(100))
    angkatan = db.Column(db.String(10))
    kelas = db.Column(db.String(50))

    ipk = db.Column(db.Numeric(4, 2))
    mengulang = db.Column(db.Integer)
    presensi = db.Column(db.Integer)
    sks_lulus = db.Column(db.Integer)

    probability = db.Column(db.Numeric(5, 2))
    risk = db.Column(db.String(20), index=True)
    recommendation = db.Column(db.Text)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("predictions", lazy=True))

    def __repr__(self):
        return f"<Prediction {self.id} {self.nim} {self.probability}%>"
