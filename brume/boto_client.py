"""Boto clients."""

import boto3
from botocore.exceptions import ClientError

from brume.config import Config


def get_region():
    return Config.load()['region']


def boto_client(service, region=None):
    return boto3.client(service, region_name=region or get_region())


def cfn_client():
    return boto_client('cloudformation')


def s3_client():
    return boto_client('s3')


def bucket_exists(bucket):
    try:
        s3_client().head_bucket(Bucket=bucket)
        return True
    except ClientError:
        return False
