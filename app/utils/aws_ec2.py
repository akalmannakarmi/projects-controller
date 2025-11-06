import boto3
import logging
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class EC2Manager:
    def __init__(self):
        self.ec2 = boto3.client(
            "ec2",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def create_instance(self, project):
        """Launch a new EC2 instance using project data."""
        try:
            response = self.ec2.run_instances(
                ImageId=project.ami_id,
                InstanceType="t3.micro",
                MinCount=1,
                MaxCount=1,
                KeyName=project.key_name,
                SecurityGroupIds=[project.security_group_id],
                SubnetId=project.subnet_id,
                UserData=project.startup_script,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [{"Key": "Name", "Value": project.name}],
                    }
                ],
            )
            instance = response["Instances"][0]
            instance_id = instance.get("InstanceId")
            logger.info(
                f"Created EC2 instance {instance_id} for project {project.name}"
            )

            # Wait until running
            self.wait_until_running(instance_id)

            public_ip = self.get_public_ip(instance_id)
            return instance_id, public_ip

        except ClientError as e:
            logger.error(f"EC2 create_instance failed: {e}")
            raise

    def wait_until_running(self, instance_id):
        """Wait for instance to reach running state."""
        waiter = self.ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])
        logger.info(f"Instance {instance_id} is running")

    def get_public_ip(self, instance_id):
        """Return the public IP of an instance."""
        response = self.ec2.describe_instances(InstanceIds=[instance_id])
        reservations = response["Reservations"]
        if not reservations:
            return None
        instance = reservations[0].get("Instances", [])[0]
        return instance.get("PublicIpAddress")

    def start_instance(self, instance_id):
        self.ec2.start_instances(InstanceIds=[instance_id])
        self.wait_until_running(instance_id)
        return self.get_public_ip(instance_id)

    def stop_instance(self, instance_id):
        self.ec2.stop_instances(InstanceIds=[instance_id])
        logger.info(f"Stopping instance {instance_id}")
        waiter = self.ec2.get_waiter("instance_stopped")
        waiter.wait(InstanceIds=[instance_id])
        logger.info(f"Instance {instance_id} stopped")

    def terminate_instance(self, instance_id):
        self.ec2.terminate_instances(InstanceIds=[instance_id])
        logger.info(f"Terminating instance {instance_id}")
        waiter = self.ec2.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=[instance_id])
        logger.info(f"Instance {instance_id} terminated")
