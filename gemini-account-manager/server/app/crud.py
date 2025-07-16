from sqlalchemy.orm import Session
from . import models, schemas
from .auth import encrypt_password

# --- User CRUD ---

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        team=user.team,
        is_security_manager=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_assigned_equipment_groups(db: Session, user_id: int) -> list[str]:
    assignments = db.query(models.UserEquipmentAssignment.equipment_group).filter(models.UserEquipmentAssignment.user_id == user_id).all()
    return [a[0] for a in assignments]


# --- EMS CRUD ---

def get_ems_systems_by_equipment_groups(db: Session, equipment_groups: list[str]):
    if not equipment_groups:
        return []
    return db.query(models.EmsSystem).filter(models.EmsSystem.equipment_group.in_(equipment_groups)).all()

def get_all_ems_systems(db: Session):
    return db.query(models.EmsSystem).all()

def create_ems_system(db: Session, system: schemas.EmsSystemCreate):
    db_system = models.EmsSystem(
        equipment_group=system.equipment_group,
        system_name=system.system_name,
        region=system.region,
        ip_url=system.ip_url
    )
    db.add(db_system)
    db.commit()
    db.refresh(db_system)

    for cred in system.credentials:
        encrypted_pw = encrypt_password(cred.password) if cred.password else None
        db_cred = models.EmsCredential(
            ems_system_id=db_system.id,
            role=cred.role,
            username=cred.username,
            encrypted_password=encrypted_pw
        )
        db.add(db_cred)
    
    db.commit()
    db.refresh(db_system)
    return db_system



# --- Server Security CRUD ---

def get_all_server_security_info(db: Session):
    return db.query(models.ServerSecurityInfo).all()

def get_server_security_info(db: Session, server_id: int):
    return db.query(models.ServerSecurityInfo).filter(models.ServerSecurityInfo.id == server_id).first()

def update_server_accounts(db: Session, server_id: int, accounts: schemas.ServerAccountUpdate):
    server = get_server_security_info(db, server_id)
    if not server:
        return None
    
    update_data = accounts.model_dump(exclude_unset=True)
    if 'primary_account_pw' in update_data and update_data['primary_account_pw']:
        server.encrypted_primary_account_pw = encrypt_password(update_data['primary_account_pw'])
    if 'root_account_pw' in update_data and update_data['root_account_pw']:
        server.encrypted_root_account_pw = encrypt_password(update_data['root_account_pw'])
    
    if 'primary_account_id' in update_data:
        server.primary_account_id = update_data['primary_account_id']
    if 'root_account_id' in update_data:
        server.root_account_id = update_data['root_account_id']
        
    db.commit()
    db.refresh(server)
    return server

def create_checklist_item(db: Session, item: schemas.SecurityChecklistItemCreate):
    db_item = models.SecurityChecklistItem(
        server_id=item.server_id,
        item_name=item.item_name,
        item_status=item.item_status
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_checklist_item(db: Session, item_id: int, item_update: schemas.SecurityChecklistItemUpdate):
    db_item = db.query(models.SecurityChecklistItem).filter(models.SecurityChecklistItem.id == item_id).first()
    if db_item:
        db_item.item_status = item_update.item_status
        db.commit()
        db.refresh(db_item)
    return db_item
