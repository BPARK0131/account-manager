from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    ForeignKey,
    Enum as SQLAlchemyEnum,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from .database import Base
import enum


# --- User Management ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    team = Column(String, nullable=False)
    is_security_manager = Column(Boolean, default=False, nullable=False)

    assigned_equipments = relationship("UserEquipmentAssignment", back_populates="user")

    __table_args__ = (
        CheckConstraint("username LIKE 'SKT%' AND LENGTH(username) = 10", name="ck_username_format"),
    )


class UserEquipmentAssignment(Base):
    __tablename__ = "user_equipment_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    equipment_group = Column(String, nullable=False)

    user = relationship("User", back_populates="assigned_equipments")


# --- EMS Management ---

class EmsSystem(Base):
    __tablename__ = "ems_systems"

    id = Column(Integer, primary_key=True, index=True)
    equipment_group = Column(String, index=True, nullable=False)
    system_name = Column(String, nullable=False)
    region = Column(String, nullable=False)
    ip_url = Column(String)

    credentials = relationship("EmsCredential", back_populates="system", cascade="all, delete-orphan")


class EmsCredentialRole(str, enum.Enum):
    system = "system"
    admin = "admin"
    viewer = "viewer"


class EmsCredential(Base):
    __tablename__ = "ems_credentials"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("ems_systems.id"), nullable=False)
    role = Column(SQLAlchemyEnum(EmsCredentialRole), nullable=False)
    username = Column(String, nullable=False)
    encrypted_password = Column(String, nullable=False)
    last_modified = Column(Date)

    system = relationship("EmsSystem", back_populates="credentials")


# --- Server Security Management ---

class ServerSecurityInfo(Base):
    __tablename__ = "server_security_info"

    id = Column(Integer, primary_key=True, index=True)
    management_id = Column(String, unique=True, index=True, nullable=False)
    server_name = Column(String)
    hostname = Column(String)
    region = Column(String)
    ip_address = Column(String)
    sgw_account_management = Column(String)
    primary_account_id = Column(String)
    encrypted_primary_account_pw = Column(String)
    root_account_id = Column(String)
    encrypted_root_account_pw = Column(String)
    vendor = Column(String)
    os_type = Column(String)
    os_version = Column(String)
    hw_model = Column(String)
    management_team = Column(String)

    checklist_items = relationship("SecurityChecklistItem", back_populates="server", cascade="all, delete-orphan")


class SecurityChecklistItem(Base):
    __tablename__ = "security_checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("server_security_info.id"), nullable=False)
    item_name = Column(String, nullable=False)
    item_status = Column(String)
    last_checked_date = Column(Date)

    server = relationship("ServerSecurityInfo", back_populates="checklist_items")
