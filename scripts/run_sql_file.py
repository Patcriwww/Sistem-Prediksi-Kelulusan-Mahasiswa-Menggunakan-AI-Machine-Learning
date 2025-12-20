from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    sql_path = 'sql/alter_add_kelas_fakultas.sql'
    print(f"Executing SQL file: {sql_path}")
    sql = open(sql_path, 'r', encoding='utf-8').read()
    try:
        with db.engine.connect() as conn:
            # Use driver-level execution to allow DO $$ blocks and multiple statements
            conn.exec_driver_sql(sql)
        print('Executed successfully')
    except Exception as e:
        print('Error executing SQL file:', e)
