"""
Brume CLI module.
"""

from glob import glob
from os import path
from yaml import dump

import click
from . import version
from .config import Config
from .stack import Stack
from .template import Template
from .assets import send_assets
from .checker import check_templates


class Context(object):
    """
    Context object to hold the configuration.
    """

    def __init__(self):
        self.config = dict()
        self.stack = None
        self.debug = False


pass_ctx = click.make_pass_decorator(Context, ensure=True)


def config_callback(ctx, _, value):
    ctx = ctx.ensure_object(Context)
    ctx.config = Config.load(value)
    ctx.stack = Stack(ctx.config['stack'])
    return value


@click.group()
@click.version_option(version, '-v', '--version')
@click.help_option('-h', '--help')
@click.option('-c', '--config', expose_value=False, default='brume.yml',
              type=click.File('r'),
              help='Configuration file (defaults to brume.yml).',
              callback=config_callback)
def cli():
    pass


@cli.command()
@pass_ctx
def config(ctx):
    """
    Print the current stack confguration.
    """
    click.echo(dump(ctx.config))


@cli.command()
@pass_ctx
def create(ctx):
    """
    Create a new CloudFormation stack.
    """
    validate_and_upload(ctx.config)
    ctx.stack.create()


@cli.command()
@pass_ctx
def update(ctx):
    """
    Update an existing CloudFormation stack.
    """
    validate_and_upload(ctx.config)
    ctx.stack.update()


@cli.command()
@pass_ctx
def deploy(ctx):
    """
    Create or update a CloudFormation stack.
    """
    validate_and_upload(ctx.config)
    ctx.stack.create_or_update()


@cli.command()
@pass_ctx
def delete(ctx):
    """
    Delete the CloudFormation stack.
    """
    ctx.stack.delete()


@cli.command()
@pass_ctx
def status(ctx):
    """
    Get the status of a CloudFormation stack.
    """
    ctx.stack.status()


@cli.command()
@pass_ctx
def outputs(ctx):
    """
    Get the full list of outputs of a CloudFormation stack.
    """
    click.echo(dump(ctx.stack.outputs(), default_flow_style=False))


@cli.command()
@pass_ctx
def parameters(ctx):
    """
    Get the full list of parameters of a CloudFormation stack.
    """
    for stack_name, stack_parameters in ctx.stack.params().items():
        if not stack_parameters:
            continue
        if ':stack/' in stack_name:
            stack_name = stack_name.partition(':stack/')[2].split('/')[0]
        click.echo(stack_name)
        for param_name, param_value in stack_parameters.items():
            click.echo('\t{} = {}'.format(param_name, param_value))
        click.echo()


@cli.command()
@pass_ctx
def validate(ctx):
    """
    Validate CloudFormation templates.
    """
    return [t.validate() for t in collect_templates(ctx.config)]


@cli.command()
@pass_ctx
def upload(ctx):
    """
    Upload CloudFormation templates and assets to S3.
    """
    process_assets(ctx.config)
    return [t.upload() for t in collect_templates(ctx.config)]


@cli.command()
@pass_ctx
def check(ctx):
    """
    Check CloudFormation templates.
    """
    check_templates(ctx.config['stack']['template_body'])


def process_assets(conf):
    """
    Upload project assets to S3.
    """
    if 'assets' not in conf:
        return
    assets_config = conf['assets']
    local_path = assets_config['local_path']
    s3_bucket = assets_config['s3_bucket']
    s3_path = assets_config['s3_path']
    click.echo("Processing assets from {} to s3://{}/{}".format(local_path, s3_bucket, s3_path))
    send_assets(local_path, s3_bucket, s3_path)


def collect_templates(conf):
    """
    Convert every template into a brume.Template.

    The type of the templates is determined based on the `template_body`
    property of the configuration file.
    """
    _file, ext = path.splitext(conf['stack']['template_body'])
    template_paths = glob(path.join(conf['templates'].get('local_path', ''), '*' + ext))
    return [Template(t, conf['templates']) for t in template_paths]


def validate_and_upload(conf):
    """
    Validate and upload CloudFormation templates to S3.
    """
    templates = collect_templates(conf)
    templates = [t.validate() for t in templates]
    templates = [t.upload() for t in templates]
    process_assets(conf)


if __name__ == '__main__':
    cli()
