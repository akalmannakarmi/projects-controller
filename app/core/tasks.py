import time
import logging
from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal
from app.db.models.project import Project
from app.utils.aws_cloudwatch import CloudWatchManager
from app.utils.aws_ec2 import EC2Manager
from app.utils.cloudflare import CloudflareManager
from app.utils.nginx_manager import NginxManager

logger = logging.getLogger(__name__)


def monitor_projects(interval: int = 300):
    """
    Background worker to monitor running projects and auto-shutdown idle instances.
    interval: check every N seconds (default 300 = 5 min)
    """
    cloudwatch = CloudWatchManager()
    ec2 = EC2Manager()
    cloudflare = CloudflareManager()
    nginx = NginxManager()
    db = None

    while True:
        try:
            db = SessionLocal()
            projects = db.query(Project).filter(Project.status == "running").all()

            for project in projects:
                # Skip if auto-shutdown is disabled
                if not project.auto_shutdown_enabled or not project.instance_id:
                    continue

                # Check network traffic in last 15 min
                traffic = cloudwatch.get_network_activity(
                    project.instance_id, minutes=15
                )

                idle_time = datetime.now(timezone.utc) - (
                    project.last_active or datetime.now(timezone.utc)
                )

                if traffic < 5000 and idle_time > timedelta(minutes=15):
                    logger.info(
                        f"Auto-shutdown: Project {project.name} idle for 15+ min"
                    )
                    ec2.terminate_instance(project.instance_id)

                    # Update Cloudflare and Nginx
                    cloudflare.revert_to_vps(project.subdomain)
                    nginx.set_state(project.name, project.subdomain, "offline")

                    # Update DB
                    project.status = "terminated"
                    project.instance_id = None
                    project.public_ip = None
                    db.commit()
                else:
                    # Update last_active timestamp if traffic detected
                    if traffic >= 5000:
                        project.last_active = datetime.now(timezone.utc)
                        db.commit()

        except Exception as e:
            logger.error(f"Error in monitor_projects: {e}")
        finally:
            if db:
                db.close()

        # Wait for next check
        time.sleep(interval)

