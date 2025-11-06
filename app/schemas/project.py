from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    subdomain: str
    ami_id: str
    security_group_id: str
    key_name: str
    subnet_id: str
    startup_script: str
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


class ProjectDetail(ProjectInDB):
    pass


class ProjectPublic(BaseModel):
    id: int
    name: str
    subdomain: str
    ami_id: str
    status: str
    public_ip: Optional[str]
    last_active: Optional[datetime]
    auto_shutdown_enabled: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
