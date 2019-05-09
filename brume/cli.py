"""
Brume CLI module.
"""

import json
from glob import glob
from os import path

import click
from brume import VERSION, config
from brume.assets import send_assets
from brume.boto_client import bucket_exists
from brume.checker import check_templates
from brume.stack import Stack
from brume.template import Template
from yaml import safe_dump


class Context:
    """
    Context object to hold the configuration.
    """

    def __init__(self):
        self.config = dict()
        self.stack = None
        self.debug = False
        self.region = None


pass_ctx = click.make_pass_decorator(Context, ensure=True)


def config_callback(ctx, _, value):
    """
    Initialize context object
    """
    ctx = ctx.ensure_object(Context)
    config.configuration_file = value
    ctx.config = config.Config.load()
    if ctx.region is None:
        ctx.region = ctx.config["region"]
    ctx.stack = Stack(ctx.region, ctx.config["stack"])
    return value


@click.group()
@click.version_option(VERSION, "-v", "--version")
@click.help_option("-h", "--help")
@click.option(
    "-c",
    "--config",
    expose_value=False,
    default=config.DEFAULT_BRUME_CONFIG,
    help="Configuration file (defaults to {}).".format(config.DEFAULT_BRUME_CONFIG),
    callback=config_callback,
)
def cli():
    """Set global cli option"""
    pass


@cli.command("config")
@pass_ctx
def config_cmd(ctx):
    """Print the current stack configuration."""
    click.echo(dump(ctx.config, default_flow_style=False))


@cli.command()
@pass_ctx
def create(ctx):
    """Create a new CloudFormation stack."""
    validate_and_upload(ctx.region, ctx.config)
    ctx.stack.create()


@cli.command()
@pass_ctx
def update(ctx):
    """Update an existing CloudFormation stack."""
    validate_and_upload(ctx.region, ctx.config)
    ctx.stack.update()


@cli.command()
@pass_ctx
def deploy(ctx):
    """Create or update a CloudFormation stack."""
    validate_and_upload(ctx.region, ctx.config)
    ctx.stack.create_or_update()
    ctx.stack.outputs()


@cli.command()
@pass_ctx
def delete(ctx):
    """Delete the CloudFormation stack."""
    ctx.stack.delete()


@cli.command()
@pass_ctx
def status(ctx):
    """Get the status of a CloudFormation stack."""
    ctx.stack.status()


output_option = click.option(
    "output_format",
    "-f",
    "--format",
    type=click.Choice(["json", "yaml"]),
    default="yaml",
    help="Output format (json/yaml)",
)


@cli.command("outputs")
@pass_ctx
@output_option
def outputs_cmd(ctx, output_format=None):
    """Get the full list of outputs of a CloudFormation stack."""
    stack_outputs = ctx.stack.outputs()
    if output_format == "yaml":
        click.echo(safe_dump(stack_outputs, default_flow_style=False))
    elif output_format == "json":
        click.echo(json.dumps(stack_outputs, indent=True))


@cli.command()
@pass_ctx
@output_option
def parameters(ctx, output_format=None):
    """Get the full list of parameters of a CloudFormation stack."""
    stack_params = ctx.stack.params()
    if output_format == "yaml":
        click.echo(safe_dump(stack_params, default_flow_style=False))
    elif output_format == "json":
        click.echo(json.dumps(stack_params, indent=True))


@cli.command()
@pass_ctx
def validate(ctx):
    """Validate CloudFormation templates."""
    error = False
    for t in collect_templates(ctx.config):
        valid = t.validate()
        if not valid:
            error = True
    if error:
        exit(1)


@cli.command()
@pass_ctx
def upload(ctx):
    """Upload CloudFormation templates and assets to S3."""
    process_assets(ctx.region, ctx.config)
    return [t.upload() for t in collect_templates(ctx.config)]


@cli.command()
@pass_ctx
def check(ctx):
    """Check CloudFormation templates."""
    check_templates(ctx.config["stack"]["template_body"])


def process_assets(region, conf):
    """Upload project assets to S3."""
    if "assets" not in conf:
        return
    assets_config = conf["assets"]
    local_path = assets_config["local_path"]
    s3_bucket = assets_config["s3_bucket"]
    s3_path = assets_config["s3_path"]
    if bucket_exists(region, s3_bucket):
        click.echo(
            "Processing assets from {} to s3://{}/{}".format(local_path, s3_bucket, s3_path)
        )
        send_assets(region, local_path, s3_bucket, s3_path)
    else:
        click.echo("Bucket does not exist {}".format(s3_bucket))


def collect_templates(conf):
    """
    Convert every template into a brume.Template.

    The type of the templates is determined based on the `template_body`
    property of the configuration file.
    """
    _file, ext = path.splitext(conf["stack"]["template_body"])
    template_paths = glob(path.join(conf["templates"].get("local_path", ""), "*" + ext))
    return [Template(t, conf["templates"]) for t in template_paths]


def validate_and_upload(region, conf):
    """Validate and upload CloudFormation templates to S3."""
    templates = collect_templates(conf)
    error = False
    for t in templates:
        if not t.validate():
            error = True
    if error:
        exit(1)
    for t in templates:
        t.upload()
    process_assets(region, conf)


if __name__ == "__main__":
    cli()
