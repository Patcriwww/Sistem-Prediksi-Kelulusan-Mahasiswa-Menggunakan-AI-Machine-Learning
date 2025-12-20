from app import create_app, db

app = create_app()

from sqlalchemy import text

with app.app_context():
    print("Applying ALTER to add students.kelas_code and FK/index if missing...")
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS kelas_code INT"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_students_kelas ON students(kelas_code)"))
            conn.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_students_kelas') THEN ALTER TABLE students ADD CONSTRAINT fk_students_kelas FOREIGN KEY (kelas_code) REFERENCES kelas(id) ON DELETE SET NULL; END IF; END$$;"))
        print("ALTER applied successfully.")
    except Exception as e:
        print("Error applying ALTER:", e)
