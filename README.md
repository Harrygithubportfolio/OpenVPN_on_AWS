OpenVPN on AWS
This repository contains scripts to automate the creation and management of an OpenVPN server on AWS. The main focus is to help users set up a secure VPN with minimal AWS knowledge.

Quick Start
1. Prerequisites
An AWS account
AWS CLI installed and configured (aws configure)
Python 3 installed, along with the required packages:
bash
Copy code
pip install boto3
2. Main Setup Script
Run the auto_setup.py script to set up the VPN server and related AWS resources:

bash
Copy code
python3 auto_setup.py
This script will:

Create a VPC with:
One public subnet (for the OpenVPN instance)
One private subnet
Set up a security group with the necessary rules for OpenVPN.
Generate a key pair for SSH access (or use an existing one in the directory).
Launch an EC2 instance with OpenVPN installed and configured.
Allocate and associate an Elastic IP for the instance.
Export all created resource details to a resources.json file for reference.
Once the script completes, you will see details about how to access the VPN server.

3. Additional Files
The following files are not necessary for running the VPN but are included for advanced users or specific needs:

1. lambda_setup.py
This script creates a Lambda function that stops the EC2 instance when its combined network usage (NetworkIn + NetworkOut) exceeds 100GB per month. The script:

Creates an IAM role for Lambda execution.
Deploys a Lambda function to stop the EC2 instance.
Sets up a CloudWatch alarm to monitor the instance's network usage and trigger the Lambda function.
Usage:

bash
Copy code
python3 lambda_setup.py
2. lambda_cleanup.py
This script deletes all resources created by the lambda_setup.py script, including:

The Lambda function
The associated IAM role
The CloudWatch alarm
Usage:

bash
Copy code
python3 lambda_cleanup.py
3. clean_up.py
This script deletes all AWS resources created by auto_setup.py, including:

The EC2 instance
Security groups
Subnets
VPC
Elastic IP
Route tables
Usage:

bash
Copy code
python3 clean_up.py
Note: Ensure the resources.json file is present in the directory, as it provides details about the resources to be deleted.

4. resources.json
This file is automatically generated by the setup scripts. It contains all resource IDs for reference and for use by cleanup or Lambda setup scripts.

4. Accessing the VPN
Navigate to the OpenVPN Admin Panel:

arduino
Copy code
https://<Elastic_IP>:943/admin
Use the credentials created during the setup process.

Download your .ovpn profile from the Client Panel:

arduino
Copy code
https://<Elastic_IP>:943/
Import the .ovpn profile into your OpenVPN client (e.g., OpenVPN Connect) and connect to your VPN.

5. Managing Costs
To avoid additional charges:

Use the clean_up.py script to delete all resources after use.
The lambda_setup.py script can help automatically shut down the instance if network usage exceeds 100GB.
6. Important Notes
Ensure your system clock is accurate to avoid issues with the OpenVPN server.
Monitor AWS usage to prevent unexpected charges.


7. Disclaimer
I am not responsible for any costs incurred by the use of this repository or the scripts within it. By using this repository, you agree to take full responsibility for monitoring and managing any charges associated with the AWS resources created. Please ensure you understand AWS pricing and usage limits before running these scripts. This is purely for educational purposes and a bit of fun.

Feel free to reach out or open an issue if you encounter any problems. Happy VPNing!