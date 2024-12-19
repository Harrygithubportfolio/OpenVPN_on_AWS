# Free OpenVPN Service on AWS

Deploy a completely free OpenVPN server on AWS with automated setup, designed to cut off after 100GB of usage for cost control.


## Instructions for Deploying the OpenVPN Script on AWS

### Follow these steps to deploy the script and set up a free OpenVPN server on AWS:

#### Prerequisites
AWS Account: Ensure you have an active AWS account.

IAM User with Admin Access: Create an IAM user with administrative permissions, or use an existing one.

AWS CLI Installed and Configured:

Install the AWS CLI ('AWS Configure' then input Public key and secret key).

Python Installed: Ensure you have Python 3.x installed on your local machine.

SSH Key Pair: Generate an SSH key pair for EC2 access, or use an existing one.

## Deployment Steps

Clone the Repository:

'mkdir OpenVpn_AWS'

cd OpenVPN_AWS

'git clone https://github.com/Harrygithubportfolio/OpenVPN_on_AWS.git '

### Install Required Python Libraries: Use pip to install the necessary dependencies:

bash
Copy code
pip install -r requirements.txt
Configure the Script:

Open the config.json file in your editor.
Update the following details:
Region: The AWS region where you want to deploy the server.
Instance Type: The EC2 instance type (e.g., t2.micro).
Key Pair Name: Your SSH key pair name for EC2 access.
Save the changes.
Run the Script: Execute the Python script to deploy the resources:

bash
Copy code
python3 deploy_openvpn.py
Wait for Deployment to Complete:

The script will create a VPC, subnets, security groups, an EC2 instance, and assign an Elastic IP.
Upon completion, it will output:
Public IP address of the OpenVPN server.
Connection credentials and configuration files.
Download OpenVPN Configuration File:

Access the server via SSH to retrieve the .ovpn configuration file.
Use the command:
bash
Copy code
scp -i /path/to/your/private-key.pem ec2-user@<Server-IP>:/home/ec2-user/<config-file>.ovpn ./local-directory
Import and Connect:

Import the .ovpn file into your OpenVPN client (e.g., OpenVPN GUI or Tunnelblick).
Connect to the VPN using the credentials.
Usage Notes
Free Tier Limitations: The VPN server is free to run under AWS Free Tier limits and cuts off after 100GB of combined data transfer (ingress and egress).
Stopping the Server: To stop incurring charges, manually stop the EC2 instance from the AWS Management Console or CLI:
bash
Copy code
aws ec2 stop-instances --instance-ids <instance-id>
Clean-Up (Optional)
To delete all resources created by the script:

Run the clean-up script:
bash
Copy code
python3 cleanup_openvpn.py
Verify that all resources (VPC, EC2 instance, Elastic IP, etc.) have been deleted from your AWS account.

##Disclaimer

This repository is provided as-is, and the scripts included are intended for educational and informational purposes only. By using this repository, you acknowledge and agree to the following:

Use at Your Own Risk: The scripts in this repository interact with AWS services and may create resources that incur costs. It is your responsibility to understand the AWS Free Tier limits and pricing before using these scripts.
No Guarantees: I make no guarantees about the functionality, accuracy, or completeness of the scripts. They are provided as a reference and may require adjustments to fit your specific needs.
No Liability: I am not responsible for any charges, fees, or costs incurred by using this repository. This includes, but is not limited to, charges for AWS services or related infrastructure.
Usage and Security: It is your responsibility to properly secure any resources created using these scripts, including managing credentials and protecting sensitive information.
By using this repository, you agree to hold me harmless from any claims, liabilities, or expenses arising from the use of these scripts.