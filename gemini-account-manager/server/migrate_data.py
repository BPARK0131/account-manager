import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

# Add the 'app' directory to the Python path to import modules from there
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.database import engine
from app.models import (
    Base,
    User,
    UserEquipmentAssignment,
    EmsSystem,
    EmsCredential,
    EmsCredentialRole,
    ServerSecurityInfo,
    SecurityChecklistItem,
)
from app.auth import get_password_hash, encrypt_password

# Load environment variables
load_dotenv()

# Setup session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def get_monthly_password():
    """Generates a password based on the current year and month, e.g., '암호_2507'."""
    now = datetime.now()
    return f"암호_{now.strftime('%y%m')}"

def migrate_ems_accounts():
    """Reads EMS account data from CSV and migrates it to the database."""
    file_path = os.path.join("..", "EMS_Account_Schema.csv")
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found. Skipping EMS accounts migration.")
        return

    print("Migrating EMS accounts...")
    df = pd.read_csv(file_path)
    
    # Rename columns for easier access
    df.columns = [
        'equipment_group', 'system_name', 'region', 'ip_url', 
        'system_id', 'system_pw', 'system_mod_date',
        'admin_id', 'admin_pw', 'admin_mod_date',
        'viewer_id', 'viewer_pw', 'viewer_mod_date'
    ]

    for _, row in df.iterrows():
        if pd.isna(row['system_name']):
            continue

        # Create EmsSystem
        ems_system = EmsSystem(
            equipment_group=row['equipment_group'],
            system_name=row['system_name'],
            region=row['region'],
            ip_url=row['ip_url']
        )
        db.add(ems_system)
        db.flush()  # Flush to get the ems_system.id for foreign key reference

        # Create EmsCredentials for system, admin, viewer
        roles = ['system', 'admin', 'viewer']
        for role in roles:
            pw = row[f'{role}_pw']
            if pd.isna(pw):
                continue
            
            if "월 자동변경" in str(pw):
                password_to_encrypt = get_monthly_password()
            else:
                password_to_encrypt = str(pw)

            credential = EmsCredential(
                system_id=ems_system.id,
                role=EmsCredentialRole[role],
                username=row[f'{role}_id'],
                encrypted_password=encrypt_password(password_to_encrypt),
                last_modified=datetime.strptime(str(row[f'{role}_mod_date']), '%y.%m.%d').date()
            )
            db.add(credential)
    print("EMS accounts migration completed.")


def migrate_server_security_info():
    """Reads server security data from CSV and migrates it to the database."""
    file_path = os.path.join("..", "Server_Security_Mgmt_Schema .csv")
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found. Skipping server security migration.")
        return

    print("Migrating server security info...")
    df = pd.read_csv(file_path, header=1) # header is on the second row

    # Define the columns for the main table (up to 'V')
    main_info_cols = df.columns[:22]
    # Define the checklist columns (from 'W' onwards)
    checklist_cols = df.columns[22:]

    for _, row in df.iterrows():
        if pd.isna(row['관리ID']):
            continue

        # Create ServerSecurityInfo
        server_info = ServerSecurityInfo(
            management_id=row['관리ID'],
            server_name=row['서버명'],
            hostname=row['장비명\n(호스트명)'],
            region=row['지역'],
            ip_address=row['IP'],
            sgw_account_management=row['SGW 계정관리'],
            primary_account_id=row['1차 계정'],
            encrypted_primary_account_pw=encrypt_password(str(row['1차 계정 비번(신)'])) if not pd.isna(row['1차 계정 비번(신)']) else None,
            root_account_id=row['root계정'],
            encrypted_root_account_pw=encrypt_password(str(row['root비번(신)'])) if not pd.isna(row['root비번(신)']) else None,
            vendor=row['벤더'],
            os_type=row['OS Type'],
            os_version=row['OS (버전도 명기)'],
            hw_model=row['HW기종'],
            management_team=row['관리']
        )
        db.add(server_info)
        db.flush()

        # Create SecurityChecklistItem for each checklist column
        for item_name in checklist_cols:
            item_status = row[item_name]
            if pd.isna(item_status):
                continue
            
            checklist_item = SecurityChecklistItem(
                server_id=server_info.id,
                item_name=item_name.strip(),
                item_status=str(item_status)
            )
            db.add(checklist_item)
    print("Server security info migration completed.")


def create_initial_users():
    """Creates a default admin and a test user."""
    print("Creating initial users...")
    
    # Check if users already exist
    admin_user = db.query(User).filter_by(username="SKT0000001").first()
    test_user = db.query(User).filter_by(username="SKT1111111").first()

    if not admin_user:
        admin = User(
            username="SKT0000001",
            hashed_password=get_password_hash("adminpassword"),
            full_name="관리자",
            team="보안팀",
            is_security_manager=True
        )
        db.add(admin)
        print("Admin user created.")

    if not test_user:
        test = User(
            username="SKT1111111",
            hashed_password=get_password_hash("testpassword"),
            full_name="테스트사용자",
            team="전송운용2팀",
            is_security_manager=False
        )
        db.add(test)
        db.flush() # Get test.id

        # Assign this user to the 'TDM' equipment group for testing
        assignment = UserEquipmentAssignment(
            user_id=test.id,
            equipment_group="TDM"
        )
        db.add(assignment)
        print("Test user and equipment assignment created.")

    print("Initial user creation completed.")


if __name__ == "__main__":
    try:
        print("--- Starting Data Migration ---")
        migrate_ems_accounts()
        migrate_server_security_info()
        create_initial_users()
        db.commit()
        print("--- Data Migration Successfully Completed ---")
    except Exception as e:
        print(f"An error occurred during migration: {e}")
        db.rollback()
        print("--- Migration Failed. All changes have been rolled back. ---")
    finally:
        db.close()
