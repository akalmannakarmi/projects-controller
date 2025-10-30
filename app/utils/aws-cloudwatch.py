import boto3
import datetime
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudWatchManager:
    def __init__(self):
        self.client = boto3.client(
            "cloudwatch",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def get_network_activity(self, instance_id: str, minutes: int = 15) -> float:
        """Return total NetworkIn + NetworkOut (bytes) in the last N minutes."""
        end_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = end_time - datetime.timedelta(minutes=minutes)

        metrics = ["NetworkIn", "NetworkOut"]
        total_bytes = 0

        for metric in metrics:
            response = self.client.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName=metric,
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 min
                Statistics=["Sum"],
            )
            datapoints = response.get("Datapoints", [])
            if datapoints:
                total_bytes += sum([dp["Sum"] for dp in datapoints])

        logger.debug(f"Total network for {instance_id}: {total_bytes} bytes")
        return total_bytes
