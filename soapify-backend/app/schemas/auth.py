from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "doctor" 
    specialization: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str