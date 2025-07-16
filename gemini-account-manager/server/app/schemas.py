from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import List, Optional
from datetime import date
import re

# --- Base and Helper Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- User Schemas ---

class UserBase(BaseModel):
    username: str = Field(..., pattern=r"^SKT\d{7}$", description="ID must be in 'SKT' + 7 digits format (e.g., SKT1234567).")
    full_name: str
    team: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters long.")

class User(UserBase):
    id: int
    is_security_manager: bool

    model_config = ConfigDict(from_attributes=True)


# --- EMS Schemas ---

class EmsSystemBase(BaseModel):
    equipment_group: str
    system_name: str
    region: str
    ip_url: Optional[str] = None

class EmsCredentialBase(BaseModel):
    role: str
    username: str

class EmsCredentialCreate(EmsCredentialBase):
    password: Optional[str] = None

class EmsSystemCreate(EmsSystemBase):
    credentials: List[EmsCredentialCreate] = []

class EmsCredential(EmsCredentialBase):
    id: int
    last_modified: Optional[date] = None
    password: Optional[str] = None # To hold decrypted password for frontend

    model_config = ConfigDict(from_attributes=True)

class EmsSystem(EmsSystemBase):
    id: int
    system_accounts: List[EmsCredential] = []
    admin_accounts: List[EmsCredential] = []
    viewer_accounts: List[EmsCredential] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    def organize_credentials(cls, data):
        if hasattr(data, 'credentials'):
            system_accounts = []
            admin_accounts = []
            viewer_accounts = []
            for cred in data.credentials:
                if cred.role.value == 'system':
                    system_accounts.append(cred)
                elif cred.role.value == 'admin':
                    admin_accounts.append(cred)
                elif cred.role.value == 'viewer':
                    viewer_accounts.append(cred)
            data.system_accounts = system_accounts
            data.admin_accounts = admin_accounts
            data.viewer_accounts = viewer_accounts
        return data


# --- Server Security Schemas ---

class SecurityChecklistItemBase(BaseModel):
    item_name: str
    item_status: str

class SecurityChecklistItemCreate(SecurityChecklistItemBase):
    server_id: int

class SecurityChecklistItemUpdate(BaseModel):
    item_status: str

class SecurityChecklistItem(SecurityChecklistItemBase):
    id: int
    last_checked_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)

class ServerSecurityInfoBase(BaseModel):
    management_id: str
    server_name: Optional[str] = None
    hostname: Optional[str] = None
    region: Optional[str] = None
    ip_address: Optional[str] = None
    vendor: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    hw_model: Optional[str] = None
    management_team: Optional[str] = None
    # Account IDs are now included for all users
    primary_account_id: Optional[str] = None
    root_account_id: Optional[str] = None

class ServerSecurityInfo(ServerSecurityInfoBase):
    id: int
    checklist_items: List[SecurityChecklistItem] = []

    model_config = ConfigDict(from_attributes=True)

class ServerAccountUpdate(BaseModel):
    primary_account_id: Optional[str] = None
    primary_account_pw: Optional[str] = None
    root_account_id: Optional[str] = None
    root_account_pw: Optional[str] = None

class ServerPasswords(BaseModel):
    primary_account_pw: Optional[str] = None
    root_account_pw: Optional[str] = None
