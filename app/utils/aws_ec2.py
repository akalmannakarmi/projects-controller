import boto3

ec2_resource = boto3.resource("ec2")


def start_instance(instanceId: str) -> None:
    instance = ec2_resource.Instance(instanceId)
    instance.start()


def stop_instance(instanceId: str) -> None:
    instance = ec2_resource.Instance(instanceId)
    instance.stop()


def instance_status(instanceId: str) -> str:
    instance = ec2_resource.Instance(instanceId)
    instance.load()
    return instance.state.get("Name") or "Unkown"
