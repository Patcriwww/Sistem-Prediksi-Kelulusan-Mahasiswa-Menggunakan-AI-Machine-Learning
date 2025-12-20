from app import create_app
from sqlalchemy import text
from extensions import db

app = create_app()
with app.app_context():
    engine = db.get_engine(app)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='students' ORDER BY ordinal_position;"))
        cols = [r[0] for r in result]
        print('students columns:', cols)
