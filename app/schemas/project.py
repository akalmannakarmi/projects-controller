from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    instanceId: str


class ProjectRead(ProjectBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ProjectDetail(ProjectRead):
    instanceId: str
