import hashlib
import secrets
from typing import Optional
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

def hash_password(password: str) -> str:
    salt = "blog_cms_salt_xyz"
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def generate_session_token() -> str:
    return secrets.token_hex(32)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get("admin_session")
    if not token:
        return None
    return db.query(User).filter(User.session_token == token).first()
