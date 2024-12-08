import boto3
import os
import time
import json

resources = {}  # Dictionary to track created resources

def save_resources_to_file(filename="resources.json"):
    """Saves the created resources to a JSON file."""
    try:
        with open(filename, "w") as file:
            json.dump(resources, file, indent=4)
        print(f"Resources saved to '{filename}'.")
    except Exception as e:
        print(f"Error saving resources to file: {e}")

def list_vpcs():
    """Lists all VPCs."""
    print("Fetching VPCs...")
    response = ec2_client.describe_vpcs()
    vpcs = response['Vpcs']
    print("\nAvailable VPCs:")
    for idx, vpc in enumerate(vpcs):
        vpc_id = vpc['VpcId']
        cidr = vpc['CidrBlock']
        is_default = vpc['IsDefault']
        tags = vpc.get('Tags', [])
        tag_info = ", ".join([f"{tag['Key']}={tag['Value']}" for tag in tags]) if tags else "No Tags"

        print(f"{idx + 1}.")
        print(f"   VPC ID: {vpc_id}")
        print(f"   CIDR Block: {cidr}")
        print(f"   Default VPC: {is_default}")
        print(f"   Tags: {tag_info}")
    return vpcs

def create_vpc():
    """Creates a new VPC with associated subnets, internet gateway, and route table."""
    print("Creating a new VPC...")
    try:
        response = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = response['Vpc']['VpcId']
        resources["vpc_id"] = vpc_id
        print(f"VPC created with ID: {vpc_id}")

        ec2_client.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": "MyNewVPC"}])

        # Create subnets
        subnet1_response = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="eu-west-2a")
        subnet2_response = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone="eu-west-2b")
        subnet1_id = subnet1_response['Subnet']['SubnetId']
        subnet2_id = subnet2_response['Subnet']['SubnetId']
        resources["subnets"] = [subnet1_id, subnet2_id]
        print(f"Subnets created: {subnet1_id}, {subnet2_id}")

        ec2_client.modify_subnet_attribute(SubnetId=subnet1_id, MapPublicIpOnLaunch={"Value": True})

        # Create an internet gateway and attach it to the VPC
        igw_response = ec2_client.create_internet_gateway()
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        resources["internet_gateway_id"] = igw_id
        print(f"Internet Gateway created and attached: {igw_id}")

        # Create a route table and associate it with the public subnet
        route_table_response = ec2_client.create_route_table(VpcId=vpc_id)
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        ec2_client.create_route(RouteTableId=route_table_id, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)
        ec2_client.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet1_id)
        resources["route_table_id"] = route_table_id
        print(f"Route table created and associated with subnet {subnet1_id}")

        return vpc_id, subnet1_id
    except Exception as e:
        print(f"Error creating VPC: {e}")
        return None, None

def create_security_group(vpc_id):
    """Creates a security group."""
    print("Creating security group...")
    try:
        response = ec2_client.create_security_group(
            GroupName="OpenVPN-Security-Group",
            Description="Security group for OpenVPN server",
            VpcId=vpc_id
        )
        sg_id = response['GroupId']
        resources["security_group_id"] = sg_id
        print(f"Security group created with ID: {sg_id}")

        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "udp", "FromPort": 1194, "ToPort": 1194, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            ],
        )
        print("Inbound rules added.")
        return sg_id
    except Exception as e:
        print(f"Error creating security group: {e}")
        return None

def create_key_pair(key_name):
    """Checks if the key pair exists, and creates it if not."""
    print(f"Checking if key pair '{key_name}' exists...")
    try:
        ec2_client.describe_key_pairs(KeyNames=[key_name])
        print(f"Key pair '{key_name}' already exists. Using it.")
        resources["key_pair_name"] = key_name
        return key_name
    except ec2_client.exceptions.ClientError as e:
        if "InvalidKeyPair.NotFound" in str(e):
            print(f"Key pair '{key_name}' does not exist. Creating it...")
            try:
                response = ec2_client.create_key_pair(KeyName=key_name)
                private_key = response['KeyMaterial']
                pem_file = f"{key_name}.pem"
                with open(pem_file, "w") as file:
                    file.write(private_key)
                os.chmod(pem_file, 0o400)
                resources["key_pair_name"] = key_name
                print(f"Key pair '{key_name}' created and saved to '{pem_file}'.")
                return key_name
            except Exception as create_error:
                print(f"Error creating key pair '{key_name}': {create_error}")
                return None
        else:
            print(f"Error checking key pair '{key_name}': {e}")
            return None

def launch_ec2_instance(key_name, sg_id, subnet_id):
    """Launches an EC2 instance."""
    print("Launching OpenVPN EC2 instance...")
    try:
        response = ec2_client.run_instances(
            ImageId="ami-031c46bb046b90dae",
            InstanceType="t2.micro",
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            SecurityGroupIds=[sg_id],
            SubnetId=subnet_id,
            TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "OpenVPN-Server"}]}],
        )
        instance_id = response["Instances"][0]["InstanceId"]
        resources["instance_id"] = instance_id
        print(f"Instance launched with ID: {instance_id}")
        return instance_id
    except Exception as e:
        print(f"Error launching EC2 instance: {e}")
        return None

def allocate_elastic_ip(instance_id):
    """Allocates and associates an Elastic IP after a delay."""
    print("Waiting 60 seconds for the EC2 instance to initialize...")
    time.sleep(60)
    print("Allocating Elastic IP...")
    try:
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        eip_response = ec2_client.allocate_address(Domain="vpc")
        ec2_client.associate_address(InstanceId=instance_id, AllocationId=eip_response["AllocationId"])
        resources["elastic_ip"] = eip_response['PublicIp']
        print(f"Elastic IP allocated: {eip_response['PublicIp']}")
    except Exception as e:
        print(f"Error allocating Elastic IP: {e}")

def main():
    print("Starting script...")
    try:
        global ec2_client
        region = input("Enter the AWS region (e.g., eu-west-2): ").strip()
        ec2_client = boto3.client("ec2", region_name=region)

        vpcs = list_vpcs()
        vpc_choice = input("Do you want to select an existing VPC? (yes/no): ").strip().lower()

        if vpc_choice == "yes":
            vpc_id = input("Enter the VPC ID to use: ").strip()
            subnet_id = input("Enter the Subnet ID to use: ").strip()
        else:
            vpc_id, subnet_id = create_vpc()
            if not vpc_id:
                print("Failed to create VPC. Exiting.")
                return

        sg_id = create_security_group(vpc_id)
        if not sg_id:
            print("Failed to create security group. Exiting.")
            return

        key_name = input("Enter the key pair name (will be created if it doesn't exist): ").strip()
        if not create_key_pair(key_name):
            print("Failed to create key pair. Exiting.")
            return

        instance_id = launch_ec2_instance(key_name, sg_id, subnet_id)
        if not instance_id:
            print("Failed to launch EC2 instance. Exiting.")
            return

        allocate_elastic_ip(instance_id)

        # Save resources to a JSON file
        save_resources_to_file()
        print("Setup completed successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
