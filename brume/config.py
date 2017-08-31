import os
from subprocess import check_output, CalledProcessError
import yaml
import click
from jinja2 import Template


class Config():

    @staticmethod
    def env(key, default=None):
        """Return the value of the `key` environment variable."""
        try:
            if default:
                return os.environ.get(key, default)
            return os.environ[key]
        except KeyError:
            click.secho('[ERROR] No environment variable with key {}'.format(key), err=True, fg='red')
            exit(1)

    @staticmethod
    def _git_commit_msg():
        """Return the message of the latest Git commit."""
        try:

            return check_output(['git', 'log', '-1', '--pretty=%B']).strip()
        except CalledProcessError:
            click.secho('[ERROR] Current directory is not a Git repository', err=True, fg='red')
            exit(1)

    @staticmethod
    def _git_commit():
        """Return the SHA1 of the latest Git commit (HEAD)."""
        try:
            return check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
        except CalledProcessError:
            click.secho('[ERROR] Current directory is not a Git repository', err=True, fg='red')
            exit(1)

    @staticmethod
    def _git_branch():
        """Return the name of the current Git branch."""
        try:
            return check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
        except CalledProcessError:
            click.secho('[ERROR] Current directory is not a Git repository', err=True, fg='red')
            exit(1)

    @staticmethod
    def git_config():
        git_config = dict(
            commit_sha1=Config._git_commit(),
            branch_name=Config._git_branch(),
            commit_msg=Config._git_commit_msg(),
        )
        return git_config

    @staticmethod
    def load(config_file):
        """
        Return the YAML configuration for a project based on the `config_file` template.

        By default, the template exposes the `env` function.
        The `git_branch` and `git_commit` values are exposed only when a `.git` folder
        exists in the current directory
        """
        template_functions = {}
        template_functions['env'] = Config.env

        if os.path.isdir('.git'):
            template_functions['git_commit'] = Config._git_commit()
            template_functions['git_branch'] = Config._git_branch()
            template_functions['git'] = Config.git_config()

        try:
            template = Template(config_file.read())
        except IOError as err:
            click.echo(err, err=True)
            exit(1)
        else:
            return yaml.load(
                template.render(**template_functions)
            )
