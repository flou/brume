"""
Assets that will be uploaded to S3 (userdata, scripts, configuration files).
"""

import os
import boto3
import click
import crayons

S3_CLIENT = boto3.client('s3')


def send_assets(local_path, s3_bucket, s3_path=''):
    """
    Send directory '{local_path}' under 's3://{s3_bucket}/{s3_path}'
    """
    for (dirpath, _dirnames, filenames) in os.walk(local_path):
        for filename in filenames:
            sourcepath = os.path.join(dirpath, filename)
            key = s3_path + '/' + os.path.relpath(sourcepath, local_path)
            click.echo('Publishing {} to {}'.format(crayons.yellow(sourcepath), s3_bucket + '/' + key))
            with click.open_file(sourcepath) as asset:
                S3_CLIENT.put_object(
                    Bucket=s3_bucket,
                    Body=asset.read(),
                    Key=key)
