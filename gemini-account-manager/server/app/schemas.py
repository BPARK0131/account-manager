from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from .models import UserRole

#=== Credential Schemas ===

class CredentialBase(BaseModel):
    service_name: str
    username: str
    url: Optional[str] = None
    notes: Optional[str] = None

class CredentialCreate(CredentialBase):
    password: str # Plain password, will be encrypted in the backend

class CredentialUpdate(BaseModel):
    service_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None

class Credential(CredentialBase):
    id: int
    owner_id: int
    password: Optional[str] = None # To hold decrypted password for frontend

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
