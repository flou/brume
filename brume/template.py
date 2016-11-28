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

    def __init__(self, file):
        self.file = file
        try:
            self.content = open(file, 'r').read()
        except IOError as e:
            print(red('File {!r} does not exist'.format(file)))
            raise e
        self.public_url = ''
        self.key = ''

    def validate(self):
        sys.stdout.write('Validating {} ... '.format(self.file))
        cfn_client = boto3.client('cloudformation')
        try:
            cfn_client.validate_template(TemplateBody=self.content)
        except ClientError as e:
            print(red('invalid'))
            print(e)
            exit(1)
        else:
            print(green('valid'))
        return self

    def upload(self, bucket, path):
        self.key = path.strip('/') + '/' + self.file
        self.public_url = 'https://{}.s3.amazonaws.com/{}'.format(
            bucket, self.key)
        print("Publishing {} to {}".format(self.file, self.public_url))
        s3_client.put_object(
            Bucket=bucket,
            Body=self.content,
            ACL='public-read',
            Key=path + '/' + self.file
        )
        return self
