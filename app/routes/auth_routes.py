from fastapi import APIRouter, HTTPException
from ..models import User
from ..schemas import UserCreate, LoginSchema, Token, UserOut
from ..utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
def register(payload: UserCreate):

    # Mobile already exists?
    if User.objects(mobile=payload.mobile).first():
        raise HTTPException(400, "Mobile already registered")

    hashed = hash_password(payload.password)

    user = User(
        username=payload.username,
        mobile=payload.mobile,
  
        password_hash=hashed
    ).save()

    return UserOut(
        id=str(user.id),
        username=user.username,
        mobile=user.mobile,

        balance=user.balance,
        role=user.role
    )


@router.post("/token", response_model=Token)
def login(payload: LoginSchema):
    user = User.objects(mobile=payload.mobile).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect mobile or password")

    token = create_access_token(str(user.id))

    return Token(access_token=token)
