from app.db.models.user import User
from app.db.session import SessionLocal
from app.core.security import get_password_hash


def create_user(email: str, password: str):
    db = SessionLocal()
    hashed_pw = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
