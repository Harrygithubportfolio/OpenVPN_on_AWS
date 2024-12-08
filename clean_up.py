import boto3
import json

def delete_resources_from_file(filename="resources.json"):
    """Reads the JSON file and deletes all resources listed in it."""
    try:
        # Load resources from the JSON file
        with open(filename, "r") as file:
            resources = json.load(file)

        print("Deleting resources from AWS...")

        # Initialize Boto3 clients
        ec2_client = boto3.client("ec2")

        # Terminate EC2 Instance
        if "instance_id" in resources:
            try:
                print(f"Terminating EC2 Instance: {resources['instance_id']}...")
                ec2_client.terminate_instances(InstanceIds=[resources["instance_id"]])
                waiter = ec2_client.get_waiter("instance_terminated")
                waiter.wait(InstanceIds=[resources["instance_id"]])
                print(f"EC2 Instance {resources['instance_id']} terminated.")
            except Exception as e:
                print(f"Error terminating EC2 Instance: {e}")

        # Delete Security Group
        if "security_group_id" in resources:
            try:
                print(f"Deleting Security Group: {resources['security_group_id']}...")
                ec2_client.delete_security_group(GroupId=resources["security_group_id"])
                print(f"Security Group {resources['security_group_id']} deleted.")
            except Exception as e:
                print(f"Error deleting Security Group: {e}")

        # Detach and delete Internet Gateway
        if "internet_gateway_id" in resources and "vpc_id" in resources:
            try:
                print(f"Detaching and deleting Internet Gateway: {resources['internet_gateway_id']}...")
                ec2_client.detach_internet_gateway(InternetGatewayId=resources["internet_gateway_id"], VpcId=resources["vpc_id"])
                ec2_client.delete_internet_gateway(InternetGatewayId=resources["internet_gateway_id"])
                print(f"Internet Gateway {resources['internet_gateway_id']} deleted.")
            except Exception as e:
                print(f"Error deleting Internet Gateway: {e}")

        # Delete Subnets
        if "subnets" in resources:
            for subnet_id in resources["subnets"]:
                try:
                    print(f"Deleting Subnet: {subnet_id}...")
                    ec2_client.delete_subnet(SubnetId=subnet_id)
                    print(f"Subnet {subnet_id} deleted.")
                except Exception as e:
                    print(f"Error deleting Subnet {subnet_id}: {e}")

        # Delete Route Table
        if "route_table_id" in resources:
            try:
                print(f"Deleting Route Table: {resources['route_table_id']}...")
                ec2_client.delete_route_table(RouteTableId=resources["route_table_id"])
                print(f"Route Table {resources['route_table_id']} deleted.")
            except Exception as e:
                print(f"Error deleting Route Table: {e}")

        # Delete VPC
        if "vpc_id" in resources:
            try:
                print(f"Deleting VPC: {resources['vpc_id']}...")
                ec2_client.delete_vpc(VpcId=resources["vpc_id"])
                print(f"VPC {resources['vpc_id']} deleted.")
            except Exception as e:
                print(f"Error deleting VPC: {e}")

        # Release Elastic IP (last step)
        if "elastic_ip" in resources:
            try:
                print(f"Releasing Elastic IP: {resources['elastic_ip']}...")
                allocation_id = ec2_client.describe_addresses(PublicIps=[resources["elastic_ip"]])["Addresses"][0]["AllocationId"]
                ec2_client.release_address(AllocationId=allocation_id)
                print(f"Elastic IP {resources['elastic_ip']} released.")
            except Exception as e:
                print(f"Error releasing Elastic IP: {e}")

        print("All resources deleted successfully.")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON file '{filename}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    delete_resources_from_file()
