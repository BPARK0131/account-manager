from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from .models import UserRole

#=== Credential Schemas ===

class CredentialBase(BaseModel):
    service_name: str
    username: str

class CredentialCreate(CredentialBase):
    password: str # Plain password, will be encrypted in the backend

class Credential(CredentialBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)

#=== User Schemas ===

class UserBase(BaseModel):
    username: str
    role: UserRole

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    credentials: List[Credential] = []

    model_config = ConfigDict(from_attributes=True)

#=== Token Schemas ===

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None
