from app import create_app, db
app = create_app()
with app.app_context():
    print('Running db.create_all()')
    db.create_all()
    print('done')