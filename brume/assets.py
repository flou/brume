import sys
import os
import boto3
import click

s3_client = boto3.client('s3')

def send_assets(local_path, s3_bucket , s3_path= ''):
    """
    Send directory '{local_path}' under 's3://{s3_bucket}/{s3_path}'
    """
    for (dirpath, dirnames, filenames) in os.walk(local_path):
        for filename in filenames:
            sourcepath = os.path.join(dirpath , filename)
            key = s3_path + '/' + os.path.relpath(sourcepath, local_path)
            click.echo('Publishing {} to {}'.format(sourcepath, s3_bucket + '/' + key))
            s3_client.put_object(
                Bucket=s3_bucket,
                Body=open(sourcepath, 'r').read(),
                Key=key
            )
