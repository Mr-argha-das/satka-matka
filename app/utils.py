from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from .config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_ctx.verify(password, hashed)

def create_access_token(subject: str, expire_minutes: int = None):
    expire_minutes = expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    to_encode = {"sub": subject}
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded
