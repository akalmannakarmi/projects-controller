import time
import logging
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.db.models.project import Project
from app.utils.aws_cloudwatch import CloudWatchManager
from app.utils.aws_ec2 import EC2Manager
from app.utils.cloudflare import CloudflareManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TRAFFIC_THRESHOLD = 50000  # bytes over 15 min considered "idle"


def monitor_projects(interval: int = 300):
    """
    Background worker to monitor running projects and auto-shutdown idle instances.
    Terminates an instance immediately if network traffic over the last 15 minutes
    is below TRAFFIC_THRESHOLD.
    """
    cloudwatch = CloudWatchManager()
    ec2 = EC2Manager()
    cloudflare = CloudflareManager()
    db = None

    logger.info("Starting project monitor loop (interval=%s sec)", interval)

    while True:
        try:
            db = SessionLocal()
            projects = db.query(Project).filter(Project.status == "running").all()
            logger.info("Found %d running projects to check", len(projects))

            for project in projects:
                logger.debug("Checking project: %s (id=%s)", project.name, project.id)

                if not project.auto_shutdown_enabled:
                    logger.debug("Skipping %s — auto-shutdown disabled", project.name)
                    continue

                if not project.instance_id:
                    logger.debug("Skipping %s — no instance_id", project.name)
                    continue

                # Get traffic data from CloudWatch
                try:
                    traffic = cloudwatch.get_network_activity(
                        project.instance_id, minutes=15
                    )
                    logger.info(
                        "Project %s traffic in last 15m: %s bytes",
                        project.name,
                        traffic,
                    )
                except Exception as exc:
                    logger.error(
                        "CloudWatch fetch failed for project %s (%s): %s",
                        project.name,
                        project.instance_id,
                        exc,
                    )
                    continue

                now = datetime.now(timezone.utc)

                # Normalize last_active just in case
                last_active = project.last_active
                if last_active is not None and last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)

                # Check for low traffic
                if traffic is None:
                    logger.warning(
                        "Traffic data missing for %s — skipping this cycle",
                        project.name,
                    )
                    continue

                if traffic < TRAFFIC_THRESHOLD:
                    logger.info(
                        "[AUTO-SHUTDOWN TRIGGERED] Project=%s | Instance=%s | Traffic=%s bytes (threshold=%s)",
                        project.name,
                        project.instance_id,
                        traffic,
                        TRAFFIC_THRESHOLD,
                    )

                    try:
                        logger.info("Terminating EC2 instance: %s", project.instance_id)
                        ec2.terminate_instance(project.instance_id)
                        logger.info(
                            "Instance %s terminated successfully", project.instance_id
                        )
                    except Exception as exc:
                        logger.error(
                            "Failed to terminate instance %s for project %s: %s",
                            project.instance_id,
                            project.name,
                            exc,
                        )
                        continue

                    # Revert Cloudflare DNS
                    try:
                        logger.info(
                            "Reverting Cloudflare to VPS for subdomain: %s",
                            project.subdomain,
                        )
                        cloudflare.revert_to_vps(project.subdomain)
                    except Exception as exc:
                        logger.error(
                            "Cloudflare revert failed for %s: %s",
                            project.subdomain,
                            exc,
                        )

                    # Update database
                    project.status = "terminated"
                    project.instance_id = None
                    project.public_ip = None
                    db.commit()
                    logger.info(
                        "Database updated — project %s marked as terminated",
                        project.name,
                    )
                    continue

                else:
                    logger.debug(
                        "Project %s is active (traffic=%s >= threshold=%s)",
                        project.name,
                        traffic,
                        TRAFFIC_THRESHOLD,
                    )
                    project.last_active = now
                    db.commit()

        except Exception as e:
            logger.exception("Unhandled error in monitor_projects: %s", e)
        finally:
            if db:
                db.close()

        logger.info("Sleeping %s seconds before next check...", interval)
        time.sleep(interval)

