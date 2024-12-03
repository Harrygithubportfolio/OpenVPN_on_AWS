# Import necessary libraries
import boto3
import json
import time

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
    subnet_id = resources.get("subnet_id")
    route_table_id = resources.get("route_table_id")
    sg_id = resources.get("sg_id")
    allocation_id = resources.get("allocation_id")

    print("Deleting resources...")
    
    # Release the Elastic IP
    print("Releasing Elastic IP...")
    try:
        ec2_client.release_address(AllocationId=allocation_id)
        print("Elastic IP released successfully.")
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

    # Delete the route table
    print("Deleting route table...")
    try:
        ec2_client.delete_route_table(RouteTableId=route_table_id)
        print("Route table deleted successfully.")
    except Exception as e:
        print(f"Error deleting route table: {str(e)}")

    # Delete the subnet
    print("Deleting subnet...")
    try:
        ec2_client.delete_subnet(SubnetId=subnet_id)
        print("Subnet deleted successfully.")
    except Exception as e:
        print(f"Error deleting subnet: {str(e)}")

    # Delete any remaining network interfaces
    print("Deleting network interfaces...")
    try:
        network_interfaces = ec2_client.describe_network_interfaces(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        for interface in network_interfaces.get('NetworkInterfaces', []):
            eni_id = interface['NetworkInterfaceId']
            ec2_client.delete_network_interface(NetworkInterfaceId=eni_id)
            print(f"Network interface {eni_id} deleted successfully.")
    except Exception as e:
        print(f"Error deleting network interfaces: {str(e)}")

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
