from pydantic import BaseModel, Field
from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

class UserCreate(BaseModel):
    username: str
    mobile: str
   
    password: str

class LoginSchema(BaseModel):
    mobile: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    username: str
    mobile: str
  
    balance: float
    role: str

class BetCreate(BaseModel):
    market: str
    number: str
    stake: float

class DrawCreate(BaseModel):
    market: str
    result_number: str



