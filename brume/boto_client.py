"""Boto clients."""

import boto3
from botocore.exceptions import ClientError


def boto_client(service, region=None):
    """
    Instanciate boto client for specified service and region
    """
    return boto3.client(service, region_name=region)


def cfn_client(region):
    """
    Instanciate cloudformation client for specified region
    """
    return boto_client('cloudformation', region)


def s3_client(region):
    """
    Instanciate S3 client for specified region
    """
    return boto_client('s3', region)


def bucket_exists(region, bucket):
    """
    Test if specified bucket exists in region
    """
    try:
        s3_client(region).head_bucket(Bucket=bucket)
        return True
    except ClientError:
        return False
