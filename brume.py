#!/usr/bin/env python

import os
import click
import yaml

from glob import glob
from brume.template import CfnTemplate
from brume.stack import Stack


def load_configuration(config_file='brume.yml'):
    from jinja2 import Template

    def env(key):
        return os.getenv(key, None)

    template = Template(open(config_file, 'r').read())
    return yaml.load(template.render(env=env))

conf = load_configuration()
s3_config = conf['templates']
cf_config = conf['stack']


def collect_templates():
    return [CfnTemplate(t) for t in glob('*.cform')]


@click.command()
def config():
    """Print the current stack confguration."""
    print(yaml.dump(conf))


@click.command()
def create():
    """Create a new CloudFormation stack."""
    stack = Stack(cf_config)
    stack.create()
    stack.tail()


@click.command()
def update():
    """Update an existing CloudFormation stack."""
    stack = Stack(cf_config)
    stack.update()
    stack.tail()


@click.command()
def deploy():
    """Create or update a CloudFormation stack."""
    stack = Stack(cf_config)
    stack.create_or_update()
    stack.tail()


@click.command()
def validate():
    """Validate CloudFormation templates."""
    templates = collect_templates()
    return map(lambda t: t.validate(), templates)


@click.command()
def events():
    """Tail the events of the stack."""
    Stack(cf_config).tail()


@click.command()
@click.option('--bucket', required=True, help='Name of the bucket')
@click.option('--prefix', required=True, help='Prefix to the file name')
def upload(templates, bucket, path_prefix):
    """Upload CloudFormation templates to S3."""
    [t.upload(bucket, path_prefix) for t in templates]
    return templates


@click.group()
def cli():
    pass

cli.add_command(create)
cli.add_command(update)
cli.add_command(deploy)
cli.add_command(upload)
cli.add_command(validate)
cli.add_command(config)
cli.add_command(events)

if __name__ == '__main__':
    cli()
