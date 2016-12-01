import os
import boto3
import sys
from colors import green, red
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')


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
            print(red('File {!r} does not exist'.format(self.file)))
            raise e

    def validate(self):
        sys.stdout.write('Validating {} ... '.format(self.file))
        cfn_client = boto3.client('cloudformation')
        try:
            cfn_client.validate_template(TemplateBody=self.content())
        except ClientError as e:
            print(red('invalid'))
            print(e)
            exit(1)
        else:
            print(green('valid'))
        return self

    def upload(self):
        print('Publishing {} to {}'.format(self.file, self.public_url))
        s3_client.put_object(
            Bucket=self.s3_bucket,
            Body=self.content(),
            Key=self.key
        )
        return self
