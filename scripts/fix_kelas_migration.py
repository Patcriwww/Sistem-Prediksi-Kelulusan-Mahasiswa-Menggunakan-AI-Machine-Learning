from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting robust migration: add students.kelas_code if missing, then index and FK.")
    with db.engine.connect() as conn:
        # Add column
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS kelas_code INT"))
            print("- ensured column students.kelas_code exists")
        except Exception as e:
            print("- error adding column:", e)

        # Add index
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_students_kelas ON students(kelas_code)"))
            print("- ensured index idx_students_kelas exists")
        except Exception as e:
            print("- error creating index:", e)

        # Ensure kelas table exists before adding FK
        try:
            r = conn.execute(text("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='kelas'"))
            if r.first():
                # Add FK constraint if not exists
                try:
                    r2 = conn.execute(text("SELECT 1 FROM pg_constraint WHERE conname = 'fk_students_kelas'"))
                    if not r2.first():
                        conn.execute(text("ALTER TABLE students ADD CONSTRAINT fk_students_kelas FOREIGN KEY (kelas_code) REFERENCES kelas(id) ON DELETE SET NULL"))
                        print("- added FK constraint fk_students_kelas")
                    else:
                        print("- FK constraint fk_students_kelas already exists")
                except Exception as e:
                    print("- error adding FK constraint:", e)
            else:
                print("- kelas table not found, skipping FK creation")
        except Exception as e:
            print("- error checking kelas table:", e)

    print("Migration done. Re-check schema with scripts/check_tables.py if needed.")
