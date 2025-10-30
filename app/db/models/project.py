from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    subdomain = Column(String, unique=True, nullable=False)  # project.example.com
    ami_id = Column(String, nullable=False)
    instance_type = Column(String, default="t3.micro")
    security_group_id = Column(String, nullable=False)
    key_name = Column(String, nullable=False)
    vpc_id = Column(String, nullable=False)
    subnet_id = Column(String, nullable=False)
    docker_image = Column(String, nullable=False)
    env_vars = Column(JSON, nullable=True)  # dict of environment vars
    auto_shutdown_enabled = Column(Boolean, default=True)
    status = Column(
        String, default="stopped"
    )  # stopped / starting / running / terminated
    last_active = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
    instance_id = Column(String, nullable=True)
    public_ip = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
