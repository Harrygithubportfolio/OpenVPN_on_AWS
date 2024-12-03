# Import necessary libraries
import boto3
import json

# Initialize the Boto3 client for EC2
ec2_client = boto3.client('ec2')

# Function to delete resources
def delete_resources(resource_file):
    # Load resource IDs from JSON file
    try:
        with open(resource_file, 'r') as f:
            resources = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{resource_file}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file '{resource_file}' could not be parsed.")
        return

    # Extract resource IDs
    instance_id = resources.get("instance_id")
    vpc_id = resources.get("vpc_id")
    igw_id = resources.get("igw_id")
    public_subnet_id = resources.get("public_subnet_id")
    private_subnet_id = resources.get("private_subnet_id")
    route_table_id = resources.get("route_table_id")
    sg_id = resources.get("sg_id")
    allocation_id = resources.get("allocation_id")

    print("Deleting resources...")

    # Disassociate and release the Elastic IP
    print("Disassociating and releasing Elastic IP...")
    try:
        ec2_client.disassociate_address(AllocationId=allocation_id)
        ec2_client.release_address(AllocationId=allocation_id)
        print("Elastic IP disassociated and released successfully.")
    except Exception as e:
        print(f"Error releasing Elastic IP: {str(e)}")

    # Terminate the EC2 instance
    print("Terminating EC2 instance...")
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[instance_id])
        print("EC2 instance terminated successfully.")
    except Exception as e:
        print(f"Error terminating EC2 instance: {str(e)}")

    # Delete the security group
    print("Deleting security group...")
    try:
        ec2_client.delete_security_group(GroupId=sg_id)
        print("Security group deleted successfully.")
    except Exception as e:
        print(f"Error deleting security group: {str(e)}")

    # Detach and delete the Internet Gateway
    print("Detaching and deleting Internet Gateway...")
    try:
        ec2_client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
        print("Internet Gateway deleted successfully.")
    except Exception as e:
        print(f"Error deleting Internet Gateway: {str(e)}")

    # Delete the subnets (both public and private)
    print("Deleting subnets...")
    try:
        ec2_client.delete_subnet(SubnetId=public_subnet_id)
        ec2_client.delete_subnet(SubnetId=private_subnet_id)
        print("Subnets deleted successfully.")
    except Exception as e:
        print(f"Error deleting subnets: {str(e)}")

    # Delete any network interfaces in the VPC
    print("Deleting any network interfaces in the VPC...")
    try:
        network_interfaces = ec2_client.describe_network_interfaces(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        for ni in network_interfaces['NetworkInterfaces']:
            ec2_client.delete_network_interface(NetworkInterfaceId=ni['NetworkInterfaceId'])
            print(f"Network Interface {ni['NetworkInterfaceId']} deleted successfully.")
    except Exception as e:
        print(f"Error deleting network interfaces: {str(e)}")

    # Delete route table
    print("Deleting route table...")
    try:
        ec2_client.delete_route_table(RouteTableId=route_table_id)
        print("Route table deleted successfully.")
    except Exception as e:
        print(f"Error deleting route table: {str(e)}")

    # Delete the VPC
    print("Deleting VPC...")
    try:
        ec2_client.delete_vpc(VpcId=vpc_id)
        print("VPC deleted successfully.")
    except Exception as e:
        print(f"Error deleting VPC: {str(e)}")

if __name__ == "__main__":
    # Specify the resource file name
    resource_file = "resources.json"

    # Call the function to delete resources
    delete_resources(resource_file)
