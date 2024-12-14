import boto3
import json

def load_resources_from_file(filename="resources.json"):
    """Loads the resources from a JSON file."""
    try:
        with open(filename, "r") as file:
            resources = json.load(file)
        print(f"Resources loaded from '{filename}'.")
        return resources
    except FileNotFoundError:
        print(f"'{filename}' not found. No resources to clean up.")
        return {}
    except Exception as e:
        print(f"Error loading resources from file: {e}")
        return {}

def safe_execute(action, resource_name, resource_id, error_message):
    """Executes an action safely with error handling."""
    try:
        action()
        print(f"{resource_name} {resource_id} deleted successfully.")
    except Exception as e:
        print(f"Error {error_message} {resource_name} {resource_id}: {e}")

def delete_cloudwatch_alarm(alarm_name):
    """Deletes a CloudWatch alarm."""
    print(f"Deleting CloudWatch Alarm: {alarm_name}...")
    safe_execute(
        lambda: cloudwatch_client.delete_alarms(AlarmNames=[alarm_name]),
        "CloudWatch Alarm",
        alarm_name,
        "deleting"
    )

def delete_lambda_function(function_name):
    """Deletes a Lambda function."""
    print(f"Deleting Lambda Function: {function_name}...")
    safe_execute(
        lambda: lambda_client.delete_function(FunctionName=function_name),
        "Lambda Function",
        function_name,
        "deleting"
    )

def terminate_ec2_instance(instance_id):
    """Terminates an EC2 instance."""
    print(f"Terminating EC2 Instance: {instance_id}...")
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        print(f"Waiting for EC2 instance {instance_id} to terminate...")
        ec2_client.get_waiter('instance_terminated').wait(InstanceIds=[instance_id])
        print(f"EC2 Instance {instance_id} terminated.")
    except Exception as e:
        print(f"Error terminating EC2 Instance {instance_id}: {e}")

def release_elastic_ip(public_ip):
    """Releases an Elastic IP."""
    print(f"Releasing Elastic IP: {public_ip}...")
    try:
        allocation_id = ec2_client.describe_addresses(PublicIps=[public_ip])["Addresses"][0]["AllocationId"]
        ec2_client.release_address(AllocationId=allocation_id)
        print(f"Elastic IP {public_ip} released.")
    except Exception as e:
        print(f"Error releasing Elastic IP {public_ip}: {e}")

def delete_security_group(sg_id):
    """Deletes a security group."""
    print(f"Deleting Security Group: {sg_id}...")
    safe_execute(
        lambda: ec2_client.delete_security_group(GroupId=sg_id),
        "Security Group",
        sg_id,
        "deleting"
    )

def detach_and_delete_internet_gateway(igw_id, vpc_id):
    """Detaches and deletes an Internet Gateway."""
    print(f"Detaching and deleting Internet Gateway: {igw_id}...")
    try:
        ec2_client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
        print(f"Internet Gateway {igw_id} deleted.")
    except Exception as e:
        print(f"Error deleting Internet Gateway {igw_id}: {e}")

def delete_subnet(subnet_id):
    """Deletes a subnet."""
    print(f"Deleting Subnet: {subnet_id}...")
    safe_execute(
        lambda: ec2_client.delete_subnet(SubnetId=subnet_id),
        "Subnet",
        subnet_id,
        "deleting"
    )

def delete_route_table(route_table_id):
    """Deletes a route table."""
    print(f"Deleting Route Table: {route_table_id}...")
    safe_execute(
        lambda: ec2_client.delete_route_table(RouteTableId=route_table_id),
        "Route Table",
        route_table_id,
        "deleting"
    )

def delete_vpc(vpc_id):
    """Deletes a VPC."""
    print(f"Deleting VPC: {vpc_id}...")
    safe_execute(
        lambda: ec2_client.delete_vpc(VpcId=vpc_id),
        "VPC",
        vpc_id,
        "deleting"
    )

def main():
    print("Deleting resources from AWS...")
    try:
        global ec2_client, lambda_client, cloudwatch_client, dynamodb_client

        # Load resources from the JSON file
        resources = load_resources_from_file()
        if not resources:
            print("No resources to delete. Exiting.")
            return

        # Determine the AWS region from the resources file
        region = resources.get("region", "eu-west-2")  # Default to "eu-west-2" if not specified
        print(f"Using region: {region}")

        # Initialize AWS clients
        ec2_client = boto3.client("ec2", region_name=region)
        lambda_client = boto3.client("lambda", region_name=region)
        cloudwatch_client = boto3.client("cloudwatch", region_name=region)
        dynamodb_client = boto3.client("dynamodb", region_name=region)

        # Delete resources in reverse order
        if "cloudwatch_alarm_name" in resources:
            delete_cloudwatch_alarm(resources["cloudwatch_alarm_name"])

        if "lambda_function_name" in resources:
            delete_lambda_function(resources["lambda_function_name"])

        if "instance_id" in resources:
            terminate_ec2_instance(resources["instance_id"])

        if "elastic_ip" in resources:
            release_elastic_ip(resources["elastic_ip"])

        if "security_group_id" in resources:
            delete_security_group(resources["security_group_id"])

        if "internet_gateway_id" in resources and "vpc_id" in resources:
            detach_and_delete_internet_gateway(resources["internet_gateway_id"], resources["vpc_id"])

        if "subnets" in resources:
            for subnet_id in resources["subnets"]:
                delete_subnet(subnet_id)

        if "route_table_id" in resources:
            delete_route_table(resources["route_table_id"])

        if "vpc_id" in resources:
            delete_vpc(resources["vpc_id"])

        print("All resources deleted successfully.")
    except Exception as e:
        print(f"An error occurred during cleanup: {e}")

if __name__ == "__main__":
    main()
