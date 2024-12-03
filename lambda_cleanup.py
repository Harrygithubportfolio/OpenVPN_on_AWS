import boto3
import time

# Initialize clients
iam_client = boto3.client('iam')
lambda_client = boto3.client('lambda')
cloudwatch_client = boto3.client('cloudwatch')

def delete_lambda_resources():
    # Lambda Function Name and IAM Role
    function_name = "StopEC2Instance"
    role_name = "LambdaStopInstanceRole"
    alarm_name = "CombinedNetworkUsageAlarm"

    print("Deleting Lambda function...")
    try:
        lambda_client.delete_function(FunctionName=function_name)
        print(f"Lambda function {function_name} deleted successfully.")
    except Exception as e:
        print(f"Error deleting Lambda function: {e}")

    print("Deleting CloudWatch alarm...")
    try:
        cloudwatch_client.delete_alarms(AlarmNames=[alarm_name])
        print(f"CloudWatch alarm {alarm_name} deleted successfully.")
    except Exception as e:
        print(f"Error deleting CloudWatch alarm: {e}")

    print("Detaching policies from IAM Role...")
    try:
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        for policy in attached_policies['AttachedPolicies']:
            iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])
            print(f"Policy {policy['PolicyArn']} detached from role {role_name}.")
    except Exception as e:
        print(f"Error detaching policies from IAM Role: {e}")

    print("Deleting IAM Role...")
    try:
        iam_client.delete_role(RoleName=role_name)
        print(f"IAM Role {role_name} deleted successfully.")
    except Exception as e:
        print(f"Error deleting IAM Role: {e}")

if __name__ == "__main__":
    delete_lambda_resources()
