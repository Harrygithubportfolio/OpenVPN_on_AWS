import boto3
import json
import os

# Initialize Boto3 clients
ec2_client = boto3.client('ec2')
iam_client = boto3.client('iam')
lambda_client = boto3.client('lambda')
cloudwatch_client = boto3.client('cloudwatch')

def create_lambda_role():
    print("Creating IAM Role for Lambda...")
    role_name = "LambdaStopInstanceRole"
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        role_arn = response['Role']['Arn']

        # Attach the EC2 stop policy to the role
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/AmazonEC2FullAccess"
        )

        # Attach Lambda execution policy to the role
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )

        print(f"IAM Role {role_name} created successfully.")
        return role_arn

    except Exception as e:
        print(f"Error creating IAM Role: {e}")
        return None

def create_lambda_function(instance_id, role_arn):
    print("Creating Lambda Function...")
    function_name = "StopEC2Instance"
    lambda_code = """
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    instance_id = event['InstanceId']
    ec2.stop_instances(InstanceIds=[instance_id])
    return {"status": "Instance stopped successfully"}
"""

    try:
        # Create the Lambda function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime="python3.8",
            Role=role_arn,
            Handler="index.lambda_handler",
            Code={"ZipFile": lambda_code.encode('utf-8')},
            Timeout=15
        )
        function_arn = response['FunctionArn']
        print(f"Lambda Function {function_name} created successfully.")
        return function_arn

    except Exception as e:
        print(f"Error creating Lambda Function: {e}")
        return None

def link_alarm_to_lambda(instance_id, function_arn):
    print("Creating CloudWatch Alarm for Network Usage...")
    alarm_name = "NetworkUsageAlarm"

    try:
        # Create the alarm
        cloudwatch_client.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription="Alarm to monitor EC2 instance network usage",
            ActionsEnabled=True,
            MetricName="NetworkOut",
            Namespace="AWS/EC2",
            Statistic="Sum",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            Period=86400,
            EvaluationPeriods=1,
            Threshold=107374182400,  # 100GB in bytes
            ComparisonOperator="GreaterThanOrEqualToThreshold",
            AlarmActions=[function_arn]
        )
        print(f"CloudWatch Alarm {alarm_name} created successfully.")

    except Exception as e:
        print(f"Error creating CloudWatch Alarm: {e}")

def main():
    # Placeholder for EC2 instance ID and other resources
    instance_id = "your-instance-id"

    # Create IAM Role for Lambda
    role_arn = create_lambda_role()
    if not role_arn:
        print("Failed to create IAM Role. Exiting.")
        return

    # Create Lambda Function
    function_arn = create_lambda_function(instance_id, role_arn)
    if not function_arn:
        print("Failed to create Lambda Function. Exiting.")
        return

    # Link CloudWatch Alarm to Lambda Function
    link_alarm_to_lambda(instance_id, function_arn)

if __name__ == "__main__":
    main()
