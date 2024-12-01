# OpenVPN on AWS - Automated Setup

This README file will walk you through setting up an OpenVPN server on AWS using a fully automated Python script. The goal is to allow anyone, even with no prior AWS experience, to create a VPN server with minimal effort.

## Prerequisites

1. **AWS CLI Installed**: Ensure that you have the AWS CLI installed on your machine. You can follow the installation guide [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

2. **AWS Credentials Configured**: Run `aws configure` to set up your AWS credentials. This script will use the credentials provided by the AWS CLI for creating and managing resources.

3. **Python 3.x**: Make sure Python 3 is installed.

4. **Boto3**: Install Boto3, the AWS SDK for Python:
   ```bash
   pip install boto3
   ```

5. **Key Pair**: You need to have an AWS EC2 key pair created. Note down the name of your key pair, as you will need to reference it in the script.

6. **VPN PEM File**: Ensure that your key pair (`vpn.pem`) is located in the same directory where you will be running the script.

## Script Overview
The provided Python script (`auto_setup.py`) automates the following steps:

1. **Create a new VPC**: Set up a Virtual Private Cloud for your OpenVPN server.
2. **Create an Internet Gateway and Subnet**: Allow internet connectivity for the instance.
3. **Launch EC2 Instance**: A t2.micro instance is created and assigned an Elastic IP.
4. **Security Group Creation**: Allow SSH (port 22) and OpenVPN (port 1194) inbound traffic.
5. **CloudWatch Alarm**: A CloudWatch alarm is created to monitor network usage (100GB threshold).
6. **OpenVPN Setup**: The script will connect to the EC2 instance and install OpenVPN.
7. **Cleanup (Optional)**: A function to delete all resources created by the script.

## How to Use the Script

### Step 1: Update the Script
Before running the script, edit `auto_setup.py` with the following changes:

1. **Replace `your_key_pair`**: Update `KeyName` in the `create_vpn_instance` function with the name of your AWS key pair.
2. **Ubuntu AMI ID**: Ensure that the `ImageId` parameter uses a valid Ubuntu AMI ID for your AWS region.

### Step 2: Run the Script
Execute the script to create and set up the VPN server:
```bash
python3 auto_setup.py
```

### Step 3: Wait for Completion
The script will output the progress of creating resources, setting up the instance, and installing OpenVPN. Once completed, you will see:
```
VPN setup complete. Instance ID: [Instance ID], Elastic IP: [Elastic IP]
```

Use the provided Elastic IP to connect to your OpenVPN server.

### Step 4: Connect to OpenVPN
To connect to your OpenVPN server:
1. Install an OpenVPN client on your local machine.
2. SSH into the EC2 instance to set up the configuration:
   ```bash
   ssh -i vpn.pem ubuntu@[Elastic IP]
   ```
3. Follow the OpenVPN configuration process to create `.ovpn` profiles.

### Step 5: Cleanup Resources (Optional)
If you want to delete all resources created by the script, you can uncomment the line at the end of `auto_setup.py`:
```python
# delete_resources(instance_id, vpc_id, igw_id, subnet_id, route_table_id, sg_id, allocation_id)
```
After uncommenting, run the script again to delete all resources.

## Troubleshooting
- **Connection Refused on SSH**: Make sure the instance is running, the security group has port 22 open, and your key pair file (`vpn.pem`) has the correct permissions (`chmod 400 vpn.pem`).
- **Elastic IP in Use Error**: Ensure that you disassociate the Elastic IP before trying to release it.

## Notes
- **AWS Costs**: This setup uses an EC2 instance, an Elastic IP, and data transfer which may incur AWS costs. Make sure to clean up resources after use to avoid unwanted charges.
- **Security**: For production use, enhance the security group rules and take necessary precautions to secure the instance.

## License
This project is licensed under the MIT License.
