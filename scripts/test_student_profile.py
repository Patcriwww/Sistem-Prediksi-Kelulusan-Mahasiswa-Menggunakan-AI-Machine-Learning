from app import create_app
from services.auth_service import get_student_profile_by_username

app = create_app()
with app.app_context():
    for username in ['mhs01','mhs06','mhs05']:
        profile = get_student_profile_by_username(username)
        print(username, '->', profile)
