import boto3
import os
import time
import json
import zipfile

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
    """Lists all VPCs along with their subnets."""
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
        print("   Subnets:")
        list_subnets(vpc_id)  # Call the function to list subnets for this VPC
    return vpcs

def list_subnets(vpc_id):
    """Lists all subnets in a given VPC."""
    try:
        response = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        subnets = response['Subnets']
        for subnet in subnets:
            subnet_id = subnet['SubnetId']
            cidr = subnet['CidrBlock']
            az = subnet['AvailabilityZone']
            is_public = subnet['MapPublicIpOnLaunch']
            print(f"      - Subnet ID: {subnet_id}, CIDR Block: {cidr}, Availability Zone: {az}, Public: {is_public}")
    except Exception as e:
        print(f"Error listing subnets for VPC {vpc_id}: {e}")


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
    """Checks if a security group exists and creates it if not."""
    group_name = "OpenVPN-Security-Group"
    print(f"Checking if security group '{group_name}' exists...")
    try:
        response = ec2_client.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [group_name]},
                {"Name": "vpc-id", "Values": [vpc_id]},
            ]
        )
        if response["SecurityGroups"]:
            sg_id = response["SecurityGroups"][0]["GroupId"]
            print(f"Security group '{group_name}' already exists with ID: {sg_id}. Using it.")
            return sg_id
    except Exception as e:
        print(f"Error checking security group: {e}")

    print(f"Security group '{group_name}' does not exist. Creating it...")
    try:
        response = ec2_client.create_security_group(
            GroupName=group_name,
            Description="Security group for OpenVPN server",
            VpcId=vpc_id
        )
        sg_id = response["GroupId"]
        resources["security_group_id"] = sg_id
        print(f"Security group created with ID: {sg_id}")

        # Add inbound rules
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "udp", "FromPort": 1194, "ToPort": 1194, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "tcp", "FromPort": 943, "ToPort": 943, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
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
                pem_file = os.path.join(os.getcwd(), f"{key_name}.pem")
                with open(pem_file, "w") as file:
                    file.write(private_key)

                # Set permissions to 600 for the PEM file
                try:
                    os.chmod(pem_file, 0o600)
                    print(f"Set permissions to 600 for '{pem_file}'.")
                except Exception as chmod_error:
                    print(f"Error setting permissions for '{pem_file}': {chmod_error}")

                resources["key_pair_name"] = key_name
                print(f"Key pair '{key_name}' created and saved to '{pem_file}'.")
                return key_name
            except Exception as create_error:
                print(f"Error creating key pair '{key_name}': {create_error}")
                return None
        else:
            print(f"Error checking key pair '{key_name}': {e}")
            return None


def ensure_iam_role_permissions(role_name):
    """Ensures the IAM role has the necessary permissions."""
    print(f"Ensuring correct permissions for IAM role: {role_name}...")
    
    try:
        # Define required managed policies
        required_policies = [
            "arn:aws:iam::aws:policy/CloudWatchFullAccess",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        ]
        
        # Check existing attached policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
        attached_policy_arns = [policy["PolicyArn"] for policy in attached_policies]

        # Attach missing policies
        for policy_arn in required_policies:
            if policy_arn not in attached_policy_arns:
                print(f"Attaching policy: {policy_arn}")
                iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        
        # Create and attach a custom inline policy for EC2 permissions
        custom_policy_name = "CustomEC2Permissions"
        custom_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:StopInstances",
                        "ec2:DescribeInstances",
                        "ec2:TerminateInstances",
                        "ec2:ReleaseAddress",
                        "ec2:DescribeAddresses"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        print(f"Attaching custom inline policy: {custom_policy_name}")
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=custom_policy_name,
            PolicyDocument=json.dumps(custom_policy_document)
        )
        print(f"Permissions for IAM role '{role_name}' updated successfully.")
    except Exception as e:
        print(f"Error ensuring permissions for IAM role '{role_name}': {e}")



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

def create_lambda_role():
    """Creates or reuses an IAM role for the Lambda function."""
    print("Creating IAM Role for Lambda...")
    role_name = "LambdaStopInstanceRole"
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    try:
        # Check if the role already exists
        response = iam_client.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        print(f"IAM Role {role_name} already exists. Reusing it.")
        return role_arn
    except iam_client.exceptions.NoSuchEntityException:
        print(f"IAM Role {role_name} does not exist. Creating it...")
        try:
            response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy)
            )
            role_arn = response["Role"]["Arn"]

            # Attach policies for Lambda execution and EC2 stop
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/AmazonEC2FullAccess"
            )

            print(f"IAM Role {role_name} created successfully. Waiting for propagation...")
            time.sleep(15)  # Wait for the role to propagate
            return role_arn
        except Exception as e:
            print(f"Error creating IAM Role: {e}")
            return None
    except Exception as e:
        print(f"Error checking IAM Role: {e}")
        return None

    # Attach managed policies
    try:
        required_policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/CloudWatchFullAccess"
        ]
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
        attached_policy_arns = [policy["PolicyArn"] for policy in attached_policies]

        for policy_arn in required_policies:
            if policy_arn not in attached_policy_arns:
                print(f"Attaching policy: {policy_arn}")
                iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

        # Attach custom inline policy for EC2 actions
        custom_policy_name = "CustomEC2Permissions"
        custom_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:StopInstances",
                        "ec2:DescribeInstances",
                        "ec2:TerminateInstances",
                        "ec2:ReleaseAddress",
                        "ec2:DescribeAddresses"
                    ],
                    "Resource": "*"
                }
            ]
        }
        print(f"Attaching custom inline policy: {custom_policy_name}")
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=custom_policy_name,
            PolicyDocument=json.dumps(custom_policy_document)
        )

        print(f"Permissions for IAM role '{role_name}' updated successfully.")
    except Exception as e:
        print(f"Error attaching policies to IAM Role '{role_name}': {e}")
        return None

    return role_arn


def create_lambda_function(instance_id, role_arn):
    """Creates the Lambda function to stop the EC2 instance."""
    print("Creating Lambda Function...")
    function_name = "StopEC2Instance"
    lambda_file = "lambda_function.zip"
    with open("lambda_function.py", "w") as file:
        file.write(f"""
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    ec2.stop_instances(InstanceIds=['{instance_id}'])
    print("Stopped instance: {instance_id}")
        """)
    with zipfile.ZipFile(lambda_file, 'w') as zip_file:
        zip_file.write("lambda_function.py")
    os.remove("lambda_function.py")

    try:
        with open(lambda_file, "rb") as file:
            zipped_code = file.read()
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime="python3.9",
            Role=role_arn,
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": zipped_code},
            Timeout=10
        )
        resources["lambda_function_name"] = function_name
        print(f"Lambda Function {function_name} created successfully.")
        return response["FunctionArn"]
    except Exception as e:
        print(f"Error creating Lambda Function: {e}")
        return None

def create_cloudwatch_alarm(instance_id, function_arn):
    """Creates a CloudWatch alarm to monitor monthly data usage."""
    print("Creating CloudWatch Alarm for monthly data usage...")
    try:
        # Define the monthly threshold split into an hourly approximation
        hourly_threshold = 107374182400 / (30 * 24)  # ~99.6 GB split into 30 days and 24 hours/day
        
        cloudwatch_client.put_metric_alarm(
            AlarmName="MonthlyDataUsageAlarm",
            AlarmDescription="Alarm to monitor combined NetworkIn and NetworkOut for ~99.6 GB of usage.",
            ActionsEnabled=True,
            AlarmActions=[function_arn],
            MetricName="NetworkOut",
            Namespace="AWS/EC2",
            Statistic="Sum",
            Period=3600,  # 1 hour
            EvaluationPeriods=24,  # Monitor for 24 hours (1 day equivalent)
            Threshold=hourly_threshold,
            ComparisonOperator="GreaterThanThreshold",
            Dimensions=[
                {"Name": "InstanceId", "Value": instance_id}
            ],
            TreatMissingData="notBreaching"
        )
        resources["cloudwatch_alarm_name"] = "VPNNetworkUsageAlarm"
        print("CloudWatch Alarm created successfully.")
    except Exception as e:
        print(f"Error creating CloudWatch Alarm: {e}")





def main():
    print("Starting script...")
    try:
        global ec2_client, iam_client, lambda_client, cloudwatch_client
        region = input("Enter the AWS region (e.g., eu-west-2): ").strip()
        resources["region"] = region  # Save the specified region to the resources dictionary
        ec2_client = boto3.client("ec2", region_name=region)
        iam_client = boto3.client("iam", region_name=region)
        lambda_client = boto3.client("lambda", region_name=region)
        cloudwatch_client = boto3.client("cloudwatch", region_name=region)

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

        role_arn = create_lambda_role()
        if not role_arn:
            print("Failed to create IAM Role. Exiting.")
            return

        function_arn = create_lambda_function(instance_id, role_arn)
        if not function_arn:
            print("Failed to create Lambda Function. Exiting.")
            return

        create_cloudwatch_alarm(instance_id, function_arn)

        save_resources_to_file()

        # Print SSH login instructions
        print_ssh_instructions()

        print("Setup completed successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")


def ssh_into_instance(pem_file, elastic_ip):
    """Uses the created .pem file to SSH into the EC2 instance."""
    print(f"Attempting to SSH into instance at {elastic_ip} using key '{pem_file}'...")
    ssh_command = f"ssh -i \"{pem_file}\" root@{elastic_ip}"
    print("\nRun the following command in your terminal to SSH into the instance:\n")
    print(ssh_command)



def print_ssh_instructions():
    """Print SSH instructions based on the existing resources."""
    try:
        # Load the resources from the JSON file
        with open("resources.json", "r") as file:
            resources = json.load(file)
        
        # Extract the Elastic IP and key pair name from resources
        elastic_ip = resources.get("elastic_ip")
        key_name = resources.get("key_pair_name")
        pem_file = os.path.abspath(f"{key_name}.pem") if key_name else None  # Get absolute path for clarity

        # Print the SSH command if both Elastic IP and key name exist
        if elastic_ip and pem_file:
            print("\nSSH Instructions:")
            print("To connect to your OpenVPN instance, run the following command:\n")
            print(f"ssh -i \"{pem_file}\" openvpnas@{elastic_ip}")
            print("\nEnsure your .pem file has the correct permissions (chmod 400) before running the command.")
        else:
            print("Elastic IP or Key Pair information is missing. Please check the resources.json file.")
    except FileNotFoundError:
        print("resources.json file not found. Ensure the VPN create script has been run successfully.")
    except Exception as e:
        print(f"An error occurred while printing SSH instructions: {e}")



if __name__ == "__main__":
    main()
