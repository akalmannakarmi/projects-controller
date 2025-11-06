from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.core.config import settings
from app.db import models
from app.api.deps import get_db, get_user
from app.schemas.basic import MessageResponse
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectPublic
from app.utils.aws_ec2 import EC2Manager
from app.utils.cloudflare import CloudflareManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=MessageResponse, status_code=201)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), _=Depends(get_user)
):
    existing = db.query(models.Project).filter_by(name=payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project already exists")

    project = models.Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)

    return {"message": "Project created"}


@router.get("/", response_model=list[ProjectPublic])
def list_projects(db: Session = Depends(get_db), _=Depends(get_user)):
    return db.query(models.Project).all()


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, db: Session = Depends(get_db), _=Depends(get_user)):
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/start", response_model=MessageResponse)
def start_project(
    project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status in ["running", "starting"]:
        return {"message": "Project is already starting"}

    ec2 = EC2Manager()
    cloudflare = CloudflareManager()

    # Step 1: update status
    project.status = "starting"
    db.commit()

    # Step 2: show starting page
    cloudflare.update_dns(project.subdomain, settings.VPS_PUBLIC_IP)

    # Step 3: Run instance creation in background
    def launch_instance():
        instance_id, public_ip = ec2.create_instance(project)
        project.instance_id = instance_id
        project.public_ip = public_ip
        project.status = "running"
        project.last_active = datetime.now(timezone.utc)
        db.add(project)
        db.commit()

        # Update DNS
        cloudflare.update_dns(project.subdomain, public_ip or "")

        logger.info(f"Project {project.name} is now running at {public_ip}")

    background_tasks.add_task(launch_instance)
    return {"message": "Project is starting"}


@router.post("/{project_id}/stop", response_model=MessageResponse)
def stop_project(project_id: int, db: Session = Depends(get_db), _=Depends(get_user)):
    project = db.query(models.Project).get(project_id)
    if not project or not project.instance_id:
        raise HTTPException(status_code=404, detail="Instance not found for project")

    ec2 = EC2Manager()
    cloudflare = CloudflareManager()

    ec2.terminate_instance(project.instance_id)
    project.status = "terminated"
    project.public_ip = None
    project.instance_id = None
    db.commit()

    cloudflare.revert_to_vps(project.subdomain)

    return {"message": "Project has been terminated"}
