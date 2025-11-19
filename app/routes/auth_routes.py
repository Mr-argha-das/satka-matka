from fastapi import APIRouter, Depends, HTTPException
from ..models import User, Transaction
from ..schemas import UserCreate, LoginSchema, Token, UserOut
from ..utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
def register(payload: UserCreate):
    if User.objects(mobile=payload.mobile).first():
        raise HTTPException(400, "Mobile already registered")
    hashed = hash_password(payload.password)
    user = User(username=payload.username, mobile=payload.mobile, password_hash=hashed).save()
    return {"id": str(user.id), "username": user.username, "mobile": user.mobile, "balance": user.balance}

@router.post("/token", response_model=Token)
def login(form_data: LoginSchema):
    user = User.objects(mobile=form_data.mobile).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}
