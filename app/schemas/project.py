from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    subdomain: str
    ami_id: str
    instance_type: Optional[str] = "t3.micro"
    security_group_id: str
    key_name: str
    vpc_id: str
    subnet_id: str
    docker_image: str
    env_vars: Optional[Dict[str, str]] = None
    auto_shutdown_enabled: bool = True


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    status: Optional[str]
    instance_id: Optional[str]
    public_ip: Optional[str]
    last_active: Optional[datetime]


class ProjectInDB(ProjectBase):
    id: int
    status: str
    last_active: Optional[datetime]
    instance_id: Optional[str]
    public_ip: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ProjectPublic(ProjectInDB):
    pass

