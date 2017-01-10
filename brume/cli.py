import click

from glob import glob
from os import path
from yaml import dump

from config import Config
from stack import Stack
from template import Template

conf = Config.load('brume.yml')
templates_config = conf['templates']
cf_config = conf['stack']


def collect_templates():
    """Convert every .cform template into a Template."""
    templates = glob(path.join(templates_config.get('local_path', ''), '*.cform'))
    return [Template(t, templates_config) for t in templates]


def validate_and_upload():
    templates = collect_templates()
    map(lambda t: t.validate(), templates)
    map(lambda t: t.upload(), templates)


@click.command()
def config():
    """Print the current stack confguration."""
    print(dump(conf))


@click.command()
def create():
    """Create a new CloudFormation stack."""
    stack = Stack(cf_config)
    validate_and_upload()
    stack.create()


@click.command()
def update():
    """Update an existing CloudFormation stack."""
    stack = Stack(cf_config)
    validate_and_upload()
    stack.update()


@click.command()
def deploy():
    """Create or update a CloudFormation stack."""
    stack = Stack(cf_config)
    validate_and_upload()
    stack.create_or_update()


@click.command()
def delete():
    """Delete a CloudFormation stack."""
    stack = Stack(cf_config)
    stack.delete()


@click.command()
def status():
    """Get the status of a CloudFormation stack."""
    Stack(cf_config).status()


@click.command()
def validate():
    """Validate CloudFormation templates."""
    templates = collect_templates()
    return map(lambda t: t.validate(), templates)


@click.command()
def upload():
    """Upload CloudFormation templates to S3."""
    templates = collect_templates()
    return map(lambda t: t.upload(), templates)


@click.group()
def cli():
    pass

cli.add_command(create)
cli.add_command(update)
cli.add_command(deploy)
cli.add_command(upload)
cli.add_command(delete)
cli.add_command(validate)
cli.add_command(config)
cli.add_command(status)

if __name__ == '__main__':
    cli()
