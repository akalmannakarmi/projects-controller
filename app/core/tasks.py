import time
import logging
from datetime import datetime, timezone, timedelta
from app.db.session import SessionLocal
from app.db.models.project import Project
from app.utils.aws_cloudwatch import CloudWatchManager
from app.utils.aws_ec2 import EC2Manager
from app.utils.cloudflare import CloudflareManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TRAFFIC_THRESHOLD = 3000  # bytes over 15 minutes considered "idle"
INACTIVITY_WINDOW = timedelta(minutes=15)


def monitor_projects(interval: int = 300):
    """
    Background worker to monitor running projects and auto-shutdown idle instances.
    - If a project has been inactive for >= 15 minutes, check CloudWatch traffic for last 15 min.
    - If traffic < TRAFFIC_THRESHOLD, terminate.
    - Else, update last_active to now.
    """
    cloudwatch = CloudWatchManager()
    ec2 = EC2Manager()
    cloudflare = CloudflareManager()

    logger.info("Starting project monitor loop (interval=%s sec)", interval)

    while True:
        db = None
        try:
            db = SessionLocal()
            projects = db.query(Project).filter(Project.status == "running").all()
            logger.info("Found %d running projects to check", len(projects))

            now = datetime.now(timezone.utc)

            for project in projects:
                logger.debug("Checking project: %s (id=%s)", project.name, project.id)

                # Skip if auto-shutdown disabled or missing instance
                if not project.auto_shutdown_enabled:
                    logger.debug("Skipping %s — auto-shutdown disabled", project.name)
                    continue
                if not project.instance_id:
                    logger.debug("Skipping %s — no instance_id", project.name)
                    continue

                # Normalize timezone
                last_active = project.last_active
                if last_active is None:
                    logger.warning(
                        "Project %s has no last_active; setting to now.", project.name
                    )
                    project.last_active = now
                    db.commit()
                    continue
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)

                # Only check CloudWatch if last_active is older than 15 minutes
                if now - last_active < INACTIVITY_WINDOW:
                    logger.debug(
                        "Skipping %s — last active %.1f minutes ago (< 15 min)",
                        project.name,
                        (now - last_active).total_seconds() / 60,
                    )
                    continue

                # Fetch CloudWatch network data
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
                        "CloudWatch fetch failed for %s (%s): %s",
                        project.name,
                        project.instance_id,
                        exc,
                    )
                    continue

                # Handle missing data
                if traffic is None:
                    logger.warning(
                        "Traffic data missing for %s — skipping this cycle",
                        project.name,
                    )
                    continue

                # Decision: terminate or refresh activity
                if traffic < TRAFFIC_THRESHOLD:
                    logger.info(
                        "[AUTO-SHUTDOWN] Project=%s | Instance=%s | Traffic=%s bytes (threshold=%s)",
                        project.name,
                        project.instance_id,
                        traffic,
                        TRAFFIC_THRESHOLD,
                    )

                    # Terminate instance
                    try:
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

                    # Revert Cloudflare
                    try:
                        cloudflare.revert_to_vps(project.subdomain)
                        logger.info("Reverted Cloudflare for %s", project.subdomain)
                    except Exception as exc:
                        logger.error(
                            "Cloudflare revert failed for %s: %s",
                            project.subdomain,
                            exc,
                        )

                    # Update DB
                    project.status = "terminated"
                    project.instance_id = None
                    project.public_ip = None
                    db.commit()
                    logger.info("Project %s marked as terminated in DB", project.name)

                else:
                    # Active — update last_active to now
                    project.last_active = now
                    db.commit()
                    logger.info(
                        "Project %s active — last_active refreshed (traffic=%s >= threshold=%s)",
                        project.name,
                        traffic,
                        TRAFFIC_THRESHOLD,
                    )

        except Exception as e:
            logger.exception("Unhandled error in monitor_projects: %s", e)
        finally:
            if db:
                db.close()

        logger.info("Sleeping %s seconds before next check...", interval)
        time.sleep(interval)

