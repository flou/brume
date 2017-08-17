"""
Template module.
"""

import os
import logging
import boto3
import click
import crayons
from botocore.exceptions import ClientError

S3_CLIENT = boto3.client('s3')
CFN_CLIENT = boto3.client('cloudformation')
CFN_TEMPLATE_SIZE_LIMIT = 51200

logging.getLogger('botocore').setLevel(logging.WARNING)


class Template(object):
    """
    CloudFormation template.
    """

    key = None

    def __init__(self, file_path, config):
        self.local_file_path = file_path
        self.file_path = file_path
        self.s3_bucket = config['s3_bucket']
        local_path = config.get('local_path', '')
        if local_path != '.':
            self.file_path = self.file_path.replace(local_path, '')
        self.s3_key = os.path.normpath('{0}/{1}'.format(
            config.get('s3_path', 'cloudformation'),
            self.file_path
        )).strip('/')
        self.public_url = self._public_url()

    def _public_url(self):
        s3_url = os.path.normpath('{0}.s3.amazonaws.com/{1}'.format(self.s3_bucket, self.s3_key))
        return 'https://{0}'.format(s3_url)

    def _content(self):
        try:
            with open(self.local_file_path, 'r') as _file:
                return _file.read()
        except IOError as err:
            click.echo(crayons.red('File {!r} does not exist').format(self.local_file_path), err=True)
            raise err

    def validate(self):
        """
        Validate the template on CloudFormation.

        If the template is larger than CFN_TEMPLATE_SIZE_LIMIT, brume uploads a
        copy of the template with the .copy suffix and performs validation on
        this template.
        """
        local_file_path = self.local_file_path
        validation_path = local_file_path
        params = {'TemplateBody': self._content()}
        if os.path.getsize(self.local_file_path) > CFN_TEMPLATE_SIZE_LIMIT:
            self.upload(copy=True)
            local_file_path = self.local_file_path + '.copy'
            validation_path = self.public_url + '.copy'
            params = {'TemplateURL': validation_path}
        try:
            click.echo('Validating {0} ...'.format(crayons.yellow(validation_path)), nl=False)
            CFN_CLIENT.validate_template(**params)
        except ClientError as err:
            click.echo(crayons.red('invalid'), err=True)
            click.echo(err.message, err=True)
            exit(1)
        else:
            click.echo(crayons.green('valid'))
        return self

    def upload(self, copy=False):
        """
        Upload the template to S3.
        If copy is True,
        """
        s3_key = self.s3_key
        public_url = self.public_url
        if copy:
            s3_key += '.copy'
            public_url += '.copy'
        click.echo('Publishing {0} to {1}'.format(crayons.yellow(self.local_file_path), public_url))
        S3_CLIENT.put_object(Bucket=self.s3_bucket, Body=self._content(), Key=s3_key)
        return self
