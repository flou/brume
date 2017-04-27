import click

from glob import glob
from os import path
from yaml import dump

from config import Config
from stack import Stack
from template import Template
from assets import send_assets
conf = Config.load('brume.yml')
templates_config = conf['templates']
cf_config = conf['stack']


def process_assets():
    if ('assets' in conf):
        assetsConfig = conf['assets']
        local_path = assetsConfig['local_path']
        s3_bucket = assetsConfig['s3_bucket']
        s3_path = assetsConfig['s3_path']
        click.echo("Processing assets from {} to s3://{}/{}".format(local_path, s3_bucket, s3_path))
        send_assets(local_path, s3_bucket , s3_path)

def collect_templates():
    """Convert every .cform template into a Template."""
    templates = glob(path.join(templates_config.get('local_path', ''), '*.cform'))
    return [Template(t, templates_config) for t in templates]


def validate_and_upload():
    templates = collect_templates()
    map(lambda t: t.validate(), templates)
    map(lambda t: t.upload(), templates)
    process_assets()


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
def outputs():
    """Get the full list of outputs of a CloudFormation stack."""
    outputs = Stack(cf_config).outputs()
    print dump(outputs, default_flow_style=False)


@click.command()
def parameters():
    """Get the full list of parameters of a CloudFormation stack."""
    parameters = Stack(cf_config).params()
    for stack_parameters in parameters:
        sp = parameters[stack_parameters]
        if not sp:
            continue
        click.echo(stack_parameters)
        for p in sp:
            click.echo('\t{} = {}'.format(p, sp[p]))
        click.echo()


@click.command()
def validate():
    """Validate CloudFormation templates."""
    templates = collect_templates()
    return map(lambda t: t.validate(), templates)


@click.command()
def upload():
    """Upload CloudFormation templates and assets to S3."""
    process_assets()
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
cli.add_command(outputs)
cli.add_command(parameters)

if __name__ == '__main__':
    cli()
