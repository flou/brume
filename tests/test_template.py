import os
import unittest

import boto3
import pytest
from brume.template import Template
from moto import mock_s3

CONFIG = {
    'region': 'eu-west-1',
    'local_path': 'test_stack',
    's3_bucket': 'dummy-bucket',
}


class TestTemplate(unittest.TestCase):
    """Test for brume.Template."""

    def setUp(self):
        self.template_path = 'tests/test_stack/main.json'
        self.template = Template(self.template_path, CONFIG)

    @mock_s3
    def test_upload(self):
        """A template can be uploaded to S3."""
        conn = boto3.resource('s3')
        conn.create_bucket(Bucket=CONFIG['s3_bucket'])
        self.template.upload()
        body = conn.Object(CONFIG['s3_bucket'], self.template.s3_key).get()['Body'].read().decode("utf-8")
        with open(self.template_path, 'r') as f:
            assert body == f.read()

    @mock_s3
    def test_upload_with_copy(self):
        """A template can be uploaded to S3."""
        conn = boto3.resource('s3')
        conn.create_bucket(Bucket=CONFIG['s3_bucket'])
        self.template.upload(copy=True)
        body = conn.Object(CONFIG['s3_bucket'], self.template.s3_key + '.copy').get()['Body'].read().decode("utf-8")
        with open(self.template_path, 'r') as f:
            assert body == f.read()

    def test_public_url(self):
        assert self.template.public_url == 'https://dummy-bucket.s3.amazonaws.com/tests/main.json'

    def test_s3_key(self):
        assert self.template.s3_key == 'tests/main.json'

    def test_public_url_with_s3_path(self):
        config = {
            'region': 'eu-west-1',
            'local_path': 'test_stack',
            's3_bucket': 'dummy-bucket',
            's3_path': 'cloudformation',
        }
        template = Template(self.template_path, config)
        assert template.public_url == 'https://dummy-bucket.s3.amazonaws.com/cloudformation/tests/main.json'

    def test_s3_key_with_s3_path(self):
        config = {
            'region': 'eu-west-1',
            'local_path': 'test_stack',
            's3_bucket': 'dummy-bucket',
            's3_path': 'cloudformation',
        }
        template = Template(self.template_path, config)
        assert template.s3_key == 'cloudformation/tests/main.json'

    def test_size(self):
        assert self.template.size == 236

    def test_content(self):
        with open(self.template_path, 'r') as f:
            assert self.template.content == f.read()

    @pytest.mark.skipif('CI' in os.environ,
                        reason="requires AWS credentials")
    def test_validate_template(self):
        bad_template = Template('tests/test_stack/invalid_stack.json', CONFIG)
        assert not bad_template.validate()
        assert self.template.validate()


if __name__ == '__main__':
    unittest.main()
