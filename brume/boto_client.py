import boto3


def cfn_client():
    return boto3.client('cloudformation')


def s3_client():
    return boto3.client('s3')
