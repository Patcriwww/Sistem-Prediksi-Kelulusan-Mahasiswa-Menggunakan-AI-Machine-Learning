from app import create_app, db
from sqlalchemy import text

app=create_app()
with app.app_context():
    with db.engine.connect() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('kelas','fakultas','students')"))
        tables = [r[0] for r in res]
        print('tables found:', tables)
        # show columns of students
        cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'students'"))
        print('students columns:', [c[0] for c in cols])
