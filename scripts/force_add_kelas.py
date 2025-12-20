from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        print('Before columns:')
        cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='students' ORDER BY ordinal_position")).fetchall()
        print([c[0] for c in cols])

        print('\nRunning ALTER TABLE public.students ADD COLUMN IF NOT EXISTS kelas_code INT;')
        try:
            conn.exec_driver_sql("ALTER TABLE public.students ADD COLUMN IF NOT EXISTS kelas_code INT;")
            print('ALTER ran OK')
        except Exception as e:
            print('ALTER error:', e)

        print('\nRunning CREATE INDEX IF NOT EXISTS idx_students_kelas ON public.students(kelas_code);')
        try:
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_students_kelas ON public.students(kelas_code);")
            print('CREATE INDEX OK')
        except Exception as e:
            print('INDEX error:', e)

        print('\nCheck FK existence')
        fk = conn.execute(text("SELECT conname FROM pg_constraint WHERE conname='fk_students_kelas'"))
        print('fk existing:', fk.fetchone())

        if not fk.fetchone():
            try:
                conn.exec_driver_sql("ALTER TABLE public.students ADD CONSTRAINT fk_students_kelas FOREIGN KEY (kelas_code) REFERENCES public.kelas(id) ON DELETE SET NULL;")
                print('Added FK')
            except Exception as e:
                print('FK add error:', e)

        print('\nAfter columns:')
        cols2 = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='students' ORDER BY ordinal_position")).fetchall()
        print([c[0] for c in cols2])
