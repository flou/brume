"""Template module."""

import logging
from os import path

import click
import crayons
from botocore.exceptions import ClientError

from brume.boto_client import cfn_client, s3_client

logging.getLogger('botocore').setLevel(logging.WARNING)

CFN_TEMPLATE_SIZE_LIMIT = 51200
DEFAULT_TEMPLATE_S3_PATH = ''
DEFAULT_TEMPLATE_LOCAL_PATH = ''
TEMPLATE_COPY_SUFFIX = '.copy'


class Template(object):
    """CloudFormation template."""

    def __init__(self, file_path, config):
        self.local_file_path = file_path
        self.file_path = file_path
        self.s3_bucket = config['s3_bucket']
        self.s3_path = config.get('s3_path', DEFAULT_TEMPLATE_S3_PATH)
        local_path = config.get('local_path', DEFAULT_TEMPLATE_LOCAL_PATH)
        if local_path != '.':
            self.file_path = self.file_path.replace(local_path, '')

    @property
    def public_url(self):
        """Return the template's public URL on S3."""
        s3_url = path.normpath('{0}.s3.amazonaws.com/{1}'.format(self.s3_bucket, self.s3_key))
        return 'https://{0}'.format(s3_url)

    @property
    def s3_key(self):
        """Return the template's key on S3."""
        return path.normpath('{0}/{1}'.format(self.s3_path, self.file_path)).strip('/')

    @property
    def size(self):
        """Return the template's file size."""
        return path.getsize(self.local_file_path)

    @property
    def template_is_too_large(self):
        """Return True if the template's file size is greater than CFN_TEMPLATE_SIZE_LIMIT."""
        return self.size > CFN_TEMPLATE_SIZE_LIMIT

    @property
    def content(self):
        """Return the template's content."""
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
        copy of the template with the .copy suffix on S3 and performs validation
        on this template.
        """
        validation_path = self.local_file_path
        params = {'TemplateBody': self.content}
        if self.template_is_too_large:
            # Template will be copied, uploaded and validated on S3
            self.upload(copy=True)
            validation_path = self.public_url + TEMPLATE_COPY_SUFFIX
            params = {'TemplateURL': validation_path}
        try:
            click.echo('Validating {0} ...'.format(crayons.yellow(validation_path)), nl=False)
            cfn_client().validate_template(**params)
        except ClientError as error:
            click.echo(crayons.red('invalid'))
            click.echo(error.message, err=True)
            return False
        click.echo(crayons.green('valid'))
        return True

    def upload(self, copy=False):
        """
        Upload the template to S3.

        If copy is True, uploads a copy of the template with the .copy suffix.
        """
        s3_key = self.s3_key
        public_url = self.public_url
        if copy:
            s3_key += TEMPLATE_COPY_SUFFIX
            public_url += TEMPLATE_COPY_SUFFIX
        click.echo('Publishing {0} to {1}'.format(crayons.yellow(self.local_file_path), public_url))
        s3_client().put_object(Bucket=self.s3_bucket, Body=self.content, Key=s3_key)
        return self
