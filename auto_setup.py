# Import necessary libraries
import boto3
import time
import os

# Initialize the Boto3 clients for EC2 and CloudWatch
ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch')

# Step 1: Create an EC2 instance and allocate an Elastic IP
def create_vpn_instance():
    # Create a new VPC
    print("Creating a new VPC...")
    vpc_response = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')
    vpc_id = vpc_response['Vpc']['VpcId']
    print(f"VPC {vpc_id} created successfully.")

    # Create an Internet Gateway and attach it to the VPC
    print("Creating and attaching an Internet Gateway...")
    igw_response = ec2_client.create_internet_gateway()
    igw_id = igw_response['InternetGateway']['InternetGatewayId']
    ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"Internet Gateway {igw_id} attached to VPC {vpc_id}.")

    # Create a subnet in the VPC
    print("Creating a subnet in the VPC...")
    subnet_response = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock='10.0.1.0/24')
    subnet_id = subnet_response['Subnet']['SubnetId']
    print(f"Subnet {subnet_id} created successfully.")

    # Create a route table and add a route to the Internet Gateway
    print("Creating a route table and adding a route to the Internet Gateway...")
    route_table_response = ec2_client.create_route_table(VpcId=vpc_id)
    route_table_id = route_table_response['RouteTable']['RouteTableId']
    ec2_client.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
    ec2_client.create_route(RouteTableId=route_table_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
    print(f"Route table {route_table_id} created and route added.")

    # Create a Security Group
    print("Creating a security group...")
    sg_response = ec2_client.create_security_group(
        GroupName='OpenVPN-SG',
        Description='Security group for OpenVPN instance',
        VpcId=vpc_id
    )
    sg_id = sg_response['GroupId']
    print(f"Security group {sg_id} created successfully.")

    # Add inbound rules to the security group
    print("Adding inbound rules to the security group...")
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'udp',
                'FromPort': 1194,
                'ToPort': 1194,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    print("Inbound rules added successfully.")

    # Launch EC2 instance
    print("Launching EC2 instance for OpenVPN...")
    response = ec2_client.run_instances(
        ImageId='ami-031c46bb046b90dae',  # Replace with a valid Ubuntu AMI
        InstanceType='t2.micro',
        KeyName='vpn',  # Replace with your EC2 key pair
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[{
            'AssociatePublicIpAddress': True,
            'DeviceIndex': 0,
            'SubnetId': subnet_id,
            'Groups': [sg_id]
        }],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': 'OpenVPN-Instance'}]
            }
        ]
    )
    instance_id = response['Instances'][0]['InstanceId']
    print(f"Instance {instance_id} launched successfully.")

    # Wait for instance to enter running state
    print("Waiting for instance to enter running state...")
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    print("Instance is now running.")

    # Allocate an Elastic IP and associate with the instance
    print("Allocating an Elastic IP...")
    elastic_ip = ec2_client.allocate_address(Domain='vpc')
    allocation_id = elastic_ip['AllocationId']
    ec2_client.associate_address(InstanceId=instance_id, AllocationId=allocation_id)
    print(f"Elastic IP allocated and associated with instance: {elastic_ip['PublicIp']}")

    return instance_id, elastic_ip['PublicIp'], vpc_id, igw_id, subnet_id, route_table_id, sg_id, allocation_id

# Step 2: Create CloudWatch Alarm to monitor network usage and trigger instance shutdown
def create_network_alarm(instance_id):
    print("Creating CloudWatch alarm for network usage...")
    cloudwatch_client.put_metric_alarm(
        AlarmName='NetworkUsageAlarm',
        AlarmDescription='Alarm for network usage above 100GB',
        ActionsEnabled=True,
        MetricName='NetworkOut',
        Namespace='AWS/EC2',
        Statistic='Sum',
        Dimensions=[
            {'Name': 'InstanceId', 'Value': instance_id}
        ],
        Period=86400,  # 1 day in seconds
        EvaluationPeriods=1,
        Threshold=107374182400,  # 100 GB
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        AlarmActions=[],  # No specific actions, just a warning
        Unit='Bytes'
    )
    print("CloudWatch alarm created successfully.")

# Step 3: Connect to instance and set up OpenVPN
# This part involves executing remote commands on the EC2 instance
def setup_openvpn(ip_address):
    print("Setting up OpenVPN on the instance...")
    setup_command = f"ssh -o StrictHostKeyChecking=no -i vpn.pem ubuntu@{ip_address} \"sudo apt update && sudo apt install openvpn -y\""
    os.system(setup_command)
    print("OpenVPN has been set up successfully on the instance.")

# Step 4: Delete resources
# This function will delete all resources created during the setup process
def delete_resources(instance_id, vpc_id, igw_id, subnet_id, route_table_id, sg_id, allocation_id):
    print("Deleting resources...")

    # Release the Elastic IP
    print("Releasing Elastic IP...")
    ec2_client.release_address(AllocationId=allocation_id)
    print("Elastic IP released.")

    # Terminate the EC2 instance
    print("Terminating EC2 instance...")
    ec2_client.terminate_instances(InstanceIds=[instance_id])
    waiter = ec2_client.get_waiter('instance_terminated')
    waiter.wait(InstanceIds=[instance_id])
    print("EC2 instance terminated.")

    # Delete the security group
    print("Deleting security group...")
    ec2_client.delete_security_group(GroupId=sg_id)
    print("Security group deleted.")

    # Detach and delete the Internet Gateway
    print("Detaching and deleting Internet Gateway...")
    ec2_client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
    print("Internet Gateway deleted.")

    # Delete the route table
    print("Deleting route table...")
    ec2_client.delete_route_table(RouteTableId=route_table_id)
    print("Route table deleted.")

    # Delete the subnet
    print("Deleting subnet...")
    ec2_client.delete_subnet(SubnetId=subnet_id)
    print("Subnet deleted.")

    # Delete the VPC
    print("Deleting VPC...")
    ec2_client.delete_vpc(VpcId=vpc_id)
    print("VPC deleted.")

    print("All resources deleted successfully.")

if __name__ == "__main__":
    # Step 1: Create the instance and allocate an Elastic IP
    instance_id, elastic_ip, vpc_id, igw_id, subnet_id, route_table_id, sg_id, allocation_id = create_vpn_instance()

    # Step 2: Set up CloudWatch alarm
    create_network_alarm(instance_id)

    # Step 3: Connect to the instance and set up OpenVPN
    setup_openvpn(elastic_ip)

    print(f"VPN setup complete. Instance ID: {instance_id}, Elastic IP: {elastic_ip}")

    # Step 4: Delete resources (uncomment the line below to execute)
   # Step 4: Delete all created resources
def delete_resources(instance_id, vpc_id, igw_id, subnet_id, route_table_id, sg_id, allocation_id):
    try:
        # Stop the instance before deleting resources
        print("Stopping the EC2 instance...")
        ec2_client.stop_instances(InstanceIds=[instance_id])
        waiter = ec2_client.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[instance_id])
        print(f"Instance {instance_id} stopped successfully.")

        # Terminate the instance
        print("Terminating the EC2 instance...")
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[instance_id])
        print(f"Instance {instance_id} terminated successfully.")

        # Disassociate and release Elastic IP
        print("Disassociating and releasing Elastic IP...")
        ec2_client.disassociate_address(AllocationId=allocation_id)
        ec2_client.release_address(AllocationId=allocation_id)
        print("Elastic IP released successfully.")

        # Delete security group
        print("Deleting security group...")
        ec2_client.delete_security_group(GroupId=sg_id)
        print(f"Security group {sg_id} deleted successfully.")

        # Detach and delete internet gateway
        print("Detaching and deleting Internet Gateway...")
        ec2_client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
        print(f"Internet Gateway {igw_id} deleted successfully.")

        # Delete route table
        print("Deleting route table...")
        ec2_client.delete_route_table(RouteTableId=route_table_id)
        print(f"Route table {route_table_id} deleted successfully.")

        # Delete subnet
        print("Deleting subnet...")
        ec2_client.delete_subnet(SubnetId=subnet_id)
        print(f"Subnet {subnet_id} deleted successfully.")

        # Delete VPC
        print("Deleting VPC...")
        ec2_client.delete_vpc(VpcId=vpc_id)
        print(f"VPC {vpc_id} deleted successfully.")

        print("All resources have been deleted successfully.")

    except Exception as e:
        print(f"An error occurred while deleting resources: {str(e)}")

