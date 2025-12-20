from models.schemas import CSV_COLUMNS
from extensions import db
from models.db_models import Prediction


# -------------------------
# DB-backed implementations
# -------------------------

def save_prediction(row: dict):
    """Save a prediction row into the DB as a Prediction record."""
    # normalize and coerce types
    rec_id = row.get("record_id")
    if not rec_id:
        rec_id = None

    p = Prediction(
        id=rec_id,
        username=row.get("username"),
        nama_mahasiswa=row.get("nama_mahasiswa"),
        nim=str(row.get("nim", "")).strip().replace(".0", ""),
        prodi=row.get("prodi"),
        angkatan=row.get("angkatan"),
        kelas=row.get("kelas"),
        ipk=(None if row.get("ipk") == "" else row.get("ipk")),
        mengulang=(None if row.get("mengulang") == "" else int(row.get("mengulang"))),
        presensi=(None if row.get("presensi") == "" else int(row.get("presensi"))),
        sks_lulus=(None if row.get("sks_lulus") == "" else int(row.get("sks_lulus"))),
        probability=(None if row.get("probability") == "" else float(row.get("probability"))),
        risk=row.get("risk"),
        recommendation=row.get("recommendation"),
    )
    db.session.add(p)
    db.session.commit()


def load_predictions() -> list[dict]:
    rows = []
    for p in Prediction.query.order_by(Prediction.timestamp).all():
        rows.append({
            "record_id": p.id,
            "username": p.username or "",
            "nama_mahasiswa": p.nama_mahasiswa or "",
            "nim": p.nim or "",
            "prodi": p.prodi or "",
            "angkatan": p.angkatan or "",
            "kelas": p.kelas or "",
            "ipk": str(p.ipk) if p.ipk is not None else "",
            "mengulang": str(p.mengulang) if p.mengulang is not None else "",
            "presensi": str(p.presensi) if p.presensi is not None else "",
            "sks_lulus": str(p.sks_lulus) if p.sks_lulus is not None else "",
            "probability": str(float(p.probability)) if p.probability is not None else "",
            "risk": p.risk or "",
            "recommendation": p.recommendation or "",
            "timestamp": p.timestamp.strftime("%Y-%m-%d %H:%M:%S") if p.timestamp else "",
        })
    return rows


def rewrite_rows(rows: list[dict]):
    # for DB backend, simplest approach: delete all and re-insert
    delete_all_predictions()
    for r in rows:
        save_prediction(r)


def delete_all_predictions():
    Prediction.query.delete()
    db.session.commit()


def delete_predictions_by_nim(nim: str):
    nim = str(nim).strip().replace(".0", "")
    Prediction.query.filter(Prediction.nim == nim).delete()
    db.session.commit()


def delete_prediction_by_id(record_id: str):
    record_id = str(record_id).strip()
    Prediction.query.filter(Prediction.id == record_id).delete()
    db.session.commit()
