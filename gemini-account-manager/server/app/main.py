
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from . import models, schemas, crud, auth
from .database import SessionLocal, engine

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware setup
origins = [
    "http://localhost:3000",  # React app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Gemini 계정 관리 플랫폼 API"}

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/credentials", response_model=schemas.Credential)
def create_credential_for_user(
    credential: schemas.CredentialCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    encrypted_password = auth.encrypt_password(credential.password)
    return crud.create_credential(
        db=db,
        credential=credential,
        encrypted_password=encrypted_password,
        owner_id=current_user.id
    )

@app.get("/credentials", response_model=List[schemas.Credential])
def read_credentials_for_user(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    credentials = crud.get_credentials_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    # Decrypt passwords before sending
    for cred in credentials:
        cred.password = auth.decrypt_password(cred.encrypted_password)
    return credentials

@app.put("/credentials/{credential_id}", response_model=schemas.Credential)
def update_credential_for_user(
    credential_id: int,
    credential: schemas.CredentialUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    encrypted_password = auth.encrypt_password(credential.password) if credential.password else None
    updated_credential = crud.update_credential(
        db=db,
        credential_id=credential_id,
        credential_update=credential,
        encrypted_password=encrypted_password,
        owner_id=current_user.id
    )
    if updated_credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    updated_credential.password = auth.decrypt_password(updated_credential.encrypted_password)
    return updated_credential

@app.delete("/credentials/{credential_id}", response_model=schemas.Credential)
def delete_credential_for_user(
    credential_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    deleted_credential = crud.delete_credential(db=db, credential_id=credential_id, owner_id=current_user.id)
    if deleted_credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    deleted_credential.password = "DELETED" # Don't need to decrypt
    return deleted_credential
