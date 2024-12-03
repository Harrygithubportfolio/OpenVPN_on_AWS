# Import necessary libraries
import boto3
import json
import time
import zipfile

# Initialize clients
iam_client = boto3.client('iam')
lambda_client = boto3.client('lambda')
cloudwatch_client = boto3.client('cloudwatch')

# Function to create the Lambda function and attach it to the CloudWatch alarm
def setup_lambda_function(resource_file):
    # Load resource IDs from the JSON file
    try:
        with open(resource_file, 'r') as f:
            resources = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{resource_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON in file '{resource_file}'.")
        return

    instance_id = resources.get("instance_id")
    if not instance_id:
        print("Error: Instance ID is missing in resources.json.")
        return

    region = "eu-west-2"

    # IAM Role setup
    role_name = "LambdaStopInstanceRole"
    print("Creating IAM Role for Lambda...")
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

    role_response = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy)
    )
    role_arn = role_response['Role']['Arn']
    print(f"IAM Role {role_name} created successfully.")

    # Attach policy to IAM Role
    print("Attaching policy to IAM Role...")
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    time.sleep(10)  # Wait for the IAM role to propagate
    print("Policy attached successfully.")

    # Lambda function code
    lambda_code = f"""
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='{region}')
    instance_id = '{instance_id}'
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id])
        print(f"Successfully initiated stopping of instance: {{instance_id}}")
        return {{
            'statusCode': 200,
            'body': f'Successfully initiated stopping of instance: {{instance_id}}'
        }}
    except Exception as e:
        print(f"Error stopping instance: {{e}}")
        return {{
            'statusCode': 500,
            'body': f'Error stopping instance: {{e}}'
        }}
    """

    # Create a zip file with the Lambda function code
    with open("lambda_function.py", "w") as f:
        f.write(lambda_code)
    zip_file = "lambda_function.zip"
    with zipfile.ZipFile(zip_file, 'w') as z:
        z.write("lambda_function.py")

    # Create Lambda function
    function_name = "StopEC2Instance"
    print("Creating Lambda Function...")
    try:
        lambda_response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.8',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': open(zip_file, 'rb').read()},
            Timeout=10,
            MemorySize=128,
        )
        print(f"Lambda Function {function_name} created successfully.")
    except Exception as e:
        print(f"Error creating Lambda Function: {e}")
        return

    # Setup CloudWatch Alarm
    print("Creating CloudWatch alarm to trigger Lambda for combined network usage...")
    try:
        cloudwatch_client.put_metric_alarm(
            AlarmName="CombinedNetworkUsageAlarm",
            AlarmDescription="Alarm for combined network usage (In + Out) above 100GB per month",
            ActionsEnabled=True,
            Metrics=[
                {
                    "Id": "network_in",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": "NetworkIn",
                            "Dimensions": [
                                {"Name": "InstanceId", "Value": instance_id}
                            ]
                        },
                        "Period": 86400,  # 1 day in seconds
                        "Stat": "Sum"
                    },
                    "ReturnData": False
                },
                {
                    "Id": "network_out",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": "NetworkOut",
                            "Dimensions": [
                                {"Name": "InstanceId", "Value": instance_id}
                            ]
                        },
                        "Period": 86400,  # 1 day in seconds
                        "Stat": "Sum"
                    },
                    "ReturnData": False
                },
                {
                    "Id": "combined_usage",
                    "Expression": "network_in + network_out",
                    "Label": "Combined Network Usage",
                    "ReturnData": True
                }
            ],
            Threshold=107374182400,  # 100 GB in bytes
            EvaluationPeriods=1,
            ComparisonOperator="GreaterThanOrEqualToThreshold",
            AlarmActions=[lambda_response['FunctionArn']],
        )
        print("CloudWatch alarm for combined network usage created successfully.")
    except Exception as e:
        print(f"Error creating CloudWatch alarm: {e}")

if __name__ == "__main__":
    # Specify the resource file
    resource_file = "resources.json"
    setup_lambda_function(resource_file)
