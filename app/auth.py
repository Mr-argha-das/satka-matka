from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from .config import settings
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_user_by_id(uid: str):
    return User.objects(id=uid).first()

def get_current_user(token: str = Depends(oauth2_scheme)):
    exc = HTTPException(401, "Could not validate credentials")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        uid = payload.get("sub")
        if not uid:
            raise exc
    except JWTError:
        raise exc

    user = get_user_by_id(uid)
    if not user:
        raise exc

    return user

def require_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return user
