# OpenVPN on AWS

This project automates the creation and cleanup of an OpenVPN server on AWS using Python and Boto3. The scripts provided help manage AWS resources such as EC2 instances, VPCs, security groups, subnets, and Elastic IPs for setting up a VPN.

## Features
- Automates the setup of an OpenVPN server on AWS.
- Automatically creates required AWS resources, including:
  - VPC
  - Subnets
  - Security Groups
  - Elastic IP
  - EC2 instance with OpenVPN installed.
- Exports created resources to a `resources.json` file for reference.
- Cleanup script to delete all created AWS resources.

## Prerequisites
- AWS CLI configured with appropriate IAM permissions.
- Python 3 installed on your system.
- `boto3` Python library installed:
  ```bash
  pip install boto3
A valid .pem file for SSH access.
Files
1. vpn_create.py
This script automates the setup of an OpenVPN server on AWS. It:

Creates a VPC and associated resources.
Launches an EC2 instance with OpenVPN installed.
Associates an Elastic IP to the instance.
Exports resource details to resources.json.
Usage
Run the script:
bash
Copy code
python3 vpn_create.py
Follow the prompts to create or select AWS resources.
2. clean_up.py
This script deletes all AWS resources created by vpn_create.py, using the resources.json file.

Usage
Run the script:
bash
Copy code
python3 clean_up.py
3. .gitignore
Specifies files to ignore in the repository, including:

.pem files.
.json files (e.g., resources.json).
Setup Instructions
Clone this repository:

bash
Copy code
git clone https://github.com/Harrygithubportfolio/OpenVPN_on_AWS.git
cd OpenVPN_on_AWS
Create an SSH key pair for the EC2 instance or use an existing one:

bash
Copy code
ssh-keygen -t rsa -b 2048 -f my-key.pem
Run the vpn_create.py script to create AWS resources and set up OpenVPN.

Cleanup Instructions
Run clean_up.py to delete all resources created by vpn_create.py. This ensures no unnecessary costs are incurred.

Security Notes
Ensure .pem and .json files are excluded from version control (.gitignore is configured to ignore them).
Avoid exposing sensitive data (e.g., AWS keys, private keys) in the repository.
Contributions
Contributions are welcome! Feel free to open an issue or submit a pull request.

**Disclaimer**
This repository is provided as-is, and the scripts included are intended for educational and informational purposes only. By using this repository, you acknowledge and agree to the following:

Use at Your Own Risk: The scripts in this repository interact with AWS services and may create resources that incur costs. It is your responsibility to understand the AWS Free Tier limits and pricing before using these scripts.
No Guarantees: I make no guarantees about the functionality, accuracy, or completeness of the scripts. They are provided as a reference and may require adjustments to fit your specific needs.
No Liability: I am not responsible for any charges, fees, or costs incurred by using this repository. This includes, but is not limited to, charges for AWS services or related infrastructure.
Usage and Security: It is your responsibility to properly secure any resources created using these scripts, including managing credentials and protecting sensitive information.
By using this repository, you agree to hold me harmless from any claims, liabilities, or expenses arising from the use of these scripts.