from pydantic import BaseModel, Field
from typing import Optional
import datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    username: str
    mobile: str
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    mobile: str
    balance: float

class LoginSchema(BaseModel):
    mobile: str
    password: str

class BetCreate(BaseModel):
    market: str
    number: str
    stake: float

class DrawCreate(BaseModel):
    market: str
    result_number: str
