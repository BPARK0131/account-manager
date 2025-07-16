from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from . import models, schemas, crud, auth
from .database import engine

app = FastAPI(
    title="Gemini Account Management Platform API",
    description="API for managing EMS and Server Security credentials.",
    version="1.0.0",
)

# CORS middleware setup
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Endpoints ---

@app.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(auth.get_db)):
    if crud.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(auth.get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- EMS Endpoints ---

@app.get("/ems-systems", response_model=List[schemas.EmsSystem])
def read_ems_systems(db: Session = Depends(auth.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.is_security_manager:
        systems = crud.get_all_ems_systems(db)
    else:
        assigned_groups = crud.get_user_assigned_equipment_groups(db, current_user.id)
        systems = crud.get_ems_systems_by_equipment_groups(db, assigned_groups)
    
    for system in systems:
        for cred in system.credentials:
            # Security managers can see all passwords.
            # Other users can only see passwords for the 'viewer' role.
            can_view_password = current_user.is_security_manager or cred.role == 'viewer'
            
            if can_view_password and cred.encrypted_password:
                try:
                    cred.password = auth.decrypt_password(cred.encrypted_password)
                except Exception:
                    cred.password = "[DECRYPTION_ERROR]"
            else:
                # Ensure password field is not sent if not authorized
                cred.password = None
    return systems


@app.post("/ems-systems", response_model=schemas.EmsSystem, status_code=status.HTTP_201_CREATED)
def create_new_ems_system(system: schemas.EmsSystemCreate, db: Session = Depends(auth.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_security_manager:
        raise HTTPException(status_code=403, detail="Not authorized to create EMS systems")
    return crud.create_ems_system(db=db, system=system)

# --- Server Security Endpoints ---

@app.get("/server-security", response_model=List[schemas.ServerSecurityInfo])
def read_server_security_info(db: Session = Depends(auth.get_db)):
    return crud.get_all_server_security_info(db)

@app.get("/server-security/{server_id}/passwords", response_model=schemas.ServerPasswords)
def get_server_passwords(server_id: int, db: Session = Depends(auth.get_db), current_user: models.User = Depends(auth.get_current_user)):
    server = crud.get_server_security_info(db, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    passwords = schemas.ServerPasswords()
    if server.encrypted_primary_account_pw:
        passwords.primary_account_pw = auth.decrypt_password(server.encrypted_primary_account_pw)
    if server.encrypted_root_account_pw:
        passwords.root_account_pw = auth.decrypt_password(server.encrypted_root_account_pw)
    return passwords

@app.put("/server-security/{server_id}/accounts", response_model=schemas.ServerSecurityInfo)
def update_server_accounts(server_id: int, accounts: schemas.ServerAccountUpdate, db: Session = Depends(auth.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_security_manager:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    updated_server = crud.update_server_accounts(db, server_id, accounts)
    if not updated_server:
        raise HTTPException(status_code=404, detail="Server not found")
    return updated_server

@app.post("/server-security/checklist-items", response_model=schemas.SecurityChecklistItem, status_code=status.HTTP_201_CREATED)
def create_new_checklist_item(item: schemas.SecurityChecklistItemCreate, db: Session = Depends(auth.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_security_manager:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.create_checklist_item(db, item)

@app.put("/server-security/checklist-items/{item_id}", response_model=schemas.SecurityChecklistItem)
def update_checklist_item_status(item_id: int, item_update: schemas.SecurityChecklistItemUpdate, db: Session = Depends(auth.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_security_manager:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    updated_item = crud.update_checklist_item(db, item_id, item_update)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return updated_item
