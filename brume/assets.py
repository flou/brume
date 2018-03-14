"""
Assets that will be uploaded to S3.

Assets can be userdata, scripts, configuration files and more.
"""

import os

import click
import crayons

from brume.boto_client import s3_client


def send_assets(region, local_path, s3_bucket, s3_path=''):
    """
    Send directory '{local_path}' under 's3://{s3_bucket}/{s3_path}'.
    """
    for (dirpath, _dirnames, filenames) in os.walk(local_path):
        for filename in filenames:
            sourcepath = os.path.join(dirpath, filename)
            key = s3_path + '/' + os.path.relpath(sourcepath, local_path)
            click.echo('Publishing {} to {}'.format(
                crayons.yellow(sourcepath), s3_bucket + '/' + key))
            with click.open_file(sourcepath) as asset:
                s3_client(region).put_object(
                    Bucket=s3_bucket, Body=asset.read(), Key=key)
