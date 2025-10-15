from datetime import datetime, timedelta, timezone
import os
import hashlib
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, UserRole


# Force use fallback for now due to bcrypt compatibility issues
pwd_context = None
BCRYPT_AVAILABLE = False
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def verify_password(plain_password: str, password_hash: str) -> bool:
    if BCRYPT_AVAILABLE:
        return pwd_context.verify(plain_password, password_hash)
    else:
        # Fallback to simple hash comparison
        return hash_password(plain_password) == password_hash


def hash_password(password: str) -> str:
    if BCRYPT_AVAILABLE:
        return pwd_context.hash(password)
    else:
        # Fallback to SHA-256 hash with salt
        salt = "coworking_booking_salt_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()


def create_access_token(subject: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = subject.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

