import os
import boto3
import sys
import click
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')

CFN_TEMPLATE_SIZE_LIMIT = 51200


class InvalidTemplateError(BaseException):

    def __init__(self, m):
        self.m = m

    def __str__(self):
        return self.m


class Template():
    key = None

    def __init__(self, file, config):
        self.file = file
        self.s3_bucket = config['s3_bucket']
        self.public_url = self.public_url(config)

    def public_url(self, config):
        local_path = config.get('local_path', '')
        if local_path != '.':
            file = self.file.replace(local_path, '')
        else:
            file = self.file
        s3_path = config.get('s3_path', 'cloudformation')
        self.key = os.path.normpath('{}/{}'.format(s3_path, file)).strip('/')
        url = os.path.normpath('{}.s3.amazonaws.com/{}'.format(self.s3_bucket, self.key))
        return 'https://{}'.format(url)

    def content(self):
        try:
            return open(self.file, 'r').read()
        except IOError as e:
            click.secho('File {!r} does not exist'.format(self.file), err=True, fg='red')
            raise e

    def validate(self):
        sys.stdout.write('Validating {} ... '.format(self.file))
        cfn_client = boto3.client('cloudformation')
        if os.path.getsize(self.file) > CFN_TEMPLATE_SIZE_LIMIT:
            params = {'TemplateURL': self.public_url}
        else:
            params = {'TemplateBody': self.content()}
        try:
            cfn_client.validate_template(**params)
        except ClientError as e:
            click.secho('invalid', err=True, fg='red')
            print(e)
            exit(1)
        else:
            click.secho('valid', fg='green')
        return self

    def upload(self):
        print('Publishing {} to {}'.format(self.file, self.public_url))
        s3_client.put_object(
            Bucket=self.s3_bucket,
            Body=self.content(),
            Key=self.key
        )
        return self
