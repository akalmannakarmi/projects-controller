from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base
from typing import Optional
from datetime import datetime


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    subdomain: Mapped[str] = mapped_column(String, unique=True)
    ami_id: Mapped[str] = mapped_column(String)
    security_group_id: Mapped[str] = mapped_column(String)
    key_name: Mapped[str] = mapped_column(String)
    subnet_id: Mapped[str] = mapped_column(String)
    startup_script: Mapped[str] = mapped_column(String)
    auto_shutdown_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String, default="stopped")
    last_active: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    instance_id: Mapped[Optional[str]] = mapped_column(String)
    public_ip: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
