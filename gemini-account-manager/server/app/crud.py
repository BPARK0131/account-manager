
from sqlalchemy.orm import Session
from . import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Credential CRUD operations

def create_credential(db: Session, credential: schemas.CredentialCreate, encrypted_password: str, owner_id: int):
    db_credential = models.Credential(
        service_name=credential.service_name,
        username=credential.username,
        encrypted_password=encrypted_password,
        owner_id=owner_id
    )
    db.add(db_credential)
    db.commit()
    db.refresh(db_credential)
    return db_credential

def get_credentials_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Credential).filter(models.Credential.owner_id == owner_id).offset(skip).limit(limit).all()
