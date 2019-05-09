"""
Configuration.

"""

import os

import click
import delegator
import jinja2
import yaml
from brume.output import stack_outputs

DEFAULT_BRUME_CONFIG = "brume.yml"
configuration_file = None


def brume_config_file():
    """
    return current brume configuration file
    """
    return configuration_file or DEFAULT_BRUME_CONFIG


# current outputs of loaded stacks
stack_outputs_definition = {}


def _check_key_exists(key, container, stack_name):
    if key not in container:
        click.secho(
            "[ERROR] No key {} variable in stack {}".format(key, stack_name), err=True, fg="red"
        )
        exit(1)


def cloudformation(region, stack_name, key, *sub_keys):
    """
    Return the value of the `key` in outputs of specified stack `stack_name`.

    If `sub_keys` is specified, return the value of the `sub_keys` found in the value of the `key`
    in outputs of specified stack `stack_name`.
    """
    if stack_name not in stack_outputs_definition:
        stack_outputs_definition[stack_name] = stack_outputs(region=region, stack_name=stack_name)
    current_definition = stack_outputs_definition[stack_name]
    _check_key_exists(key, current_definition, stack_name)
    current_definition = current_definition[key]

    for subKey in sub_keys:
        _check_key_exists(subKey, current_definition, stack_name)
        current_definition = current_definition[subKey]

    return current_definition


def is_installed(cmd):
    """Check that ``cmd`` is installed and available in $PATH."""
    c = delegator.run([cmd])
    if c.err:
        return False
    return True


def is_git_repo():
    """Check that the current directory is a functioning git repository."""
    c = delegator.run("git status")
    if "fatal: Not a git repository" in c.err:
        return False
    return True


class Config:
    """Configuration."""

    config = {}

    @staticmethod
    def cfn(region, stack_name, key, second_key=None, third_key=None):
        """Return the value of the `key` output of stack_name cloud formation stack.
           cfn methods will lookup recursively in nested stack if second_key (and third_key) is provided.
        """
        if second_key is None:
            return cloudformation(region, stack_name, key)
        if third_key is None:
            return cloudformation(region, stack_name, key, second_key)
        return cloudformation(region, stack_name, key, second_key, third_key)

    @staticmethod
    def env(key, default=None):
        """Return the value of the `key` environment variable."""
        try:
            if default:
                return os.getenv(key, default)
            return os.environ[key]
        except KeyError:
            click.secho(
                "[ERROR] No environment variable with key {}".format(key), err=True, fg="red"
            )
            exit(1)

    @staticmethod
    def _git_commit_msg():
        """
        Return the message (subject) of the latest Git commit.

        YAML complains if the commit message contains single quotes, so we
        remove those.
        """
        c = delegator.run("git log -1 --pretty=%s")
        return c.out.strip().replace("'", "")

    @staticmethod
    def _git_commit():
        """Return the SHA1 of the latest Git commit (HEAD)."""
        c = delegator.run("git rev-parse --short HEAD")
        return c.out.strip()

    @staticmethod
    def _git_branch():
        """Return the name of the current Git branch."""
        c = delegator.run("git rev-parse --abbrev-ref HEAD")
        return c.out.strip()

    @staticmethod
    def git_config():
        """Return the Git configuration if the current directory is a Git repo."""
        if not is_installed("git"):
            click.secho("[WARN] git is not installed or not in $PATH", err=True, fg="red")
            return {}
        if not is_git_repo():
            click.secho("[WARN] Current directory is not a Git repository", err=True, fg="red")
            return {}
        return dict(
            branch_name=Config._git_branch(),
            commit_sha1=Config._git_commit(),
            commit_msg=Config._git_commit_msg(),
        )

    @classmethod
    def load(cls, config_file=None):
        """
        Return the YAML configuration for a project based on the `config_file` template.

        By default, the template exposes the `env` function.
        The `git_branch` and `git_commit` values are exposed only when a `.git` folder
        exists in the current directory
        """
        config_file = config_file or brume_config_file()
        if not Config.config:
            template = Config.render(config_file)
            template_env = dict(
                cfn=Config.cfn,
                env=Config.env,
                git=Config.git_config(),
                git_branch=Config._git_branch(),
                git_commit=Config._git_commit(),
            )
            try:
                Config.config = yaml.load(template.render(**template_env))
            except jinja2.exceptions.UndefinedError as err:
                click.secho(
                    "[ERROR] {0} in {1}".format(err.message, config_file), err=True, fg="red"
                )
                exit(1)
            except KeyError as err:
                click.secho("[ERROR] {0} in {1}".format(err, config_file), err=True, fg="red")
                exit(1)
        return Config.config

    @staticmethod
    def render(config_file):
        """Render config_file as a Jinja template."""
        path, filename = os.path.split(os.path.abspath(config_file))
        try:
            return jinja2.Environment(
                loader=jinja2.FileSystemLoader(path or "./"), undefined=jinja2.StrictUndefined
            ).get_template(filename)
        except jinja2.exceptions.TemplateNotFound:
            click.secho(
                "[ERROR] No such file or directory: {0}".format(config_file), err=True, fg="red"
            )
            exit(1)
