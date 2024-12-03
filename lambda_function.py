
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='eu-west-2')
    instance_id = 'i-00ec8b1846068d564'
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id])
        print(f"Successfully initiated stopping of instance: {instance_id}")
        return {
            'statusCode': 200,
            'body': f'Successfully initiated stopping of instance: {instance_id}'
        }
    except Exception as e:
        print(f"Error stopping instance: {e}")
        return {
            'statusCode': 500,
            'body': f'Error stopping instance: {e}'
        }
    