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

'pip install -r requirements.txt'


Configure the Script:

Run the Script: Execute the Python script to deploy the resources:


python3 deploy_openvpn.py

Wait for Deployment to Complete:

The script will create a VPC, subnets, security groups, an EC2 instance, and assign an Elastic IP. It will also create lambda functions to turn the instance off at 100GB per month. However it has been configured differently. The alarm evaluates the metric in 1-hour intervals (Period = 3600 seconds).
It triggers if the hourly data consistently exceeds the threshold over a 24-hour evaluation period.

Upon completion, it will output:
Public IP address of the OpenVPN server.
Connection credentials and configuration files.
Download OpenVPN Configuration File:

Access the server via SSH to retrieve the .ovpn configuration file.

Use the command:

'scp -i /path/to/your/private-key.pem ec2-user@<Server-IP>:/home/ec2-user/<config-file>.ovpn ./local-directory'

Follow the instructions after logging into the instance to correctly configure the openvpn server to your requirements. 

You will then need to log in to the admin panel and get an activation code. Then you will need to log in to the openvpn portal and get the .ovpn file to import into your client.

Usage Notes

Free Tier Limitations: The VPN server is free to run under AWS Free Tier limits and cuts off after 100GB of combined data transfer (ingress and egress).

Stopping the Server: To stop incurring charges, manually stop the EC2 instance from the AWS Management Console or CLI:

Clean-Up (Optional)
To delete all resources created by the script:

Run the clean-up script:


python3 cleanup_openvpn.py
Verify that all resources (VPC, EC2 instance, Elastic IP, etc.) have been deleted from your AWS account.

## Disclaimer

This repository is provided as-is, and the scripts included are intended for educational and informational purposes only. By using this repository, you acknowledge and agree to the following:

Use at Your Own Risk: The scripts in this repository interact with AWS services and may create resources that incur costs. It is your responsibility to understand the AWS Free Tier limits and pricing before using these scripts.
No Guarantees: I make no guarantees about the functionality, accuracy, or completeness of the scripts. They are provided as a reference and may require adjustments to fit your specific needs.
No Liability: I am not responsible for any charges, fees, or costs incurred by using this repository. This includes, but is not limited to, charges for AWS services or related infrastructure.
Usage and Security: It is your responsibility to properly secure any resources created using these scripts, including managing credentials and protecting sensitive information.
By using this repository, you agree to hold me harmless from any claims, liabilities, or expenses arising from the use of these scripts.
