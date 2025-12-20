import bcrypt
from typing import Optional, Dict, List

from models.db_models import User, Student, ClassModel
from extensions import db


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode()


def check_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode())
    except Exception:
        return False


# -------------------------
# DB-backed helpers
# -------------------------

def get_user_by_username(username: str) -> Optional[User]:
    if not username:
        return None
    return User.query.filter_by(username=username).first()


def create_user(username: str, password: str, role: str = "mahasiswa") -> User:
    h = hash_pw(password)
    u = User(username=username, password_hash=h, role=role)
    db.session.add(u)
    db.session.commit()
    return u


def get_student_profile_by_username(username: str) -> Optional[Dict]:
    """Return a dict similar to previous STUDENT_PROFILES value or None."""
    user = get_user_by_username(username)
    if user and getattr(user, "student", None):
        s = user.student
        return {
            "nama_mahasiswa": s.nama_mahasiswa,
            "nim": s.nim,
            "prodi": s.prodi,
            "angkatan": s.angkatan,
            "kelas": s.kelas_code,
        }
    # fallback: try find student by nim=username
    s = Student.query.filter_by(nim=str(username).strip()).first()
    if s:
        return {
            "nama_mahasiswa": s.nama_mahasiswa,
            "nim": s.nim,
            "prodi": s.prodi,
            "angkatan": s.angkatan,
            "kelas": s.kelas_code,
        }
    return None


def get_class_by_code(code: str) -> Optional[ClassModel]:
    if not code:
        return None
    return ClassModel.query.filter_by(code=code).first()


def get_students_by_class_code(code: str) -> List[str]:
    cls = get_class_by_code(code)
    if not cls:
        return []
    return [s.nim for s in Student.query.filter_by(kelas_code=code).all()]

