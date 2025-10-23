from os import stat
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Project
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectRead, ProjectStatus
from app.api.deps import get_db, get_user
from app.utils.aws_ec2 import start_instance, stop_instance, instance_status

router = APIRouter()


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    _=Depends(get_user),
):
    result = await db.execute(select(Project).offset(skip).limit(limit))
    projects = result.scalars().all()
    return projects


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_user),
):
    project = Project(**project_in.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: int,
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_data = project_in.model_dump(exclude_unset=True)
    for key, value in project_data.items():
        setattr(project, key, value)

    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return


@router.post("/{project_id}/start", status_code=status.HTTP_200_OK)
async def start_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        start_instance(str(project.instanceId))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to start project")

    return


@router.post("/{project_id}/stop", status_code=status.HTTP_200_OK)
async def stop_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        stop_instance(str(project.instanceId))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to stop project")

    return


@router.get("/{project_id}/status", response_model=ProjectStatus)
async def project_status(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        projectStatus = instance_status(str(project.instanceId))
        return {"status": projectStatus}
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to get project status")
