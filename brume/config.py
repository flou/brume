"""
Configuration.

"""

import os

import click
import delegator
import yaml
import jinja2


def is_installed(cmd):
    """Check that ``cmd`` is installed and available in $PATH."""
    c = delegator.run([cmd])
    if c.err:
        return False
    return True


def is_git_repo():
    """Check that the current directory is a functioning git repository."""
    c = delegator.run('git status')
    if 'fatal: Not a git repository' in c.err:
        return False
    return True


class Config():

    @staticmethod
    def env(key, default=None):
        """Return the value of the `key` environment variable."""
        try:
            if default:
                return os.getenv(key, default)
            return os.environ[key]
        except KeyError:
            click.secho('[ERROR] No environment variable with key {}'.format(key), err=True, fg='red')
            exit(1)

    @staticmethod
    def _git_commit_msg():
        """
        Return the message (subject) of the latest Git commit.

        YAML complains if the commit message contains single quotes, so we
        remove those.
        """
        c = delegator.run('git log -1 --pretty=%s')
        return c.out.strip().replace('\'', '')

    @staticmethod
    def _git_commit():
        """Return the SHA1 of the latest Git commit (HEAD)."""
        c = delegator.run('git rev-parse --short HEAD')
        return c.out.strip()

    @staticmethod
    def _git_branch():
        """Return the name of the current Git branch."""
        c = delegator.run('git rev-parse --abbrev-ref HEAD')
        return c.out.strip()

    @staticmethod
    def git_config():
        if not is_installed('git'):
            click.secho('[WARN] git is not installed or not in $PATH', err=True, fg='red')
            return {}
        if not is_git_repo():
            click.secho('[ERROR] Current directory is not a Git repository', err=True, fg='red')
            return {}
        return dict(
            branch_name=Config._git_branch(),
            commit_sha1=Config._git_commit(),
            commit_msg=Config._git_commit_msg()
        )

    @staticmethod
    def load(config_file):
        """
        Return the YAML configuration for a project based on the `config_file` template.

        By default, the template exposes the `env` function.
        The `git_branch` and `git_commit` values are exposed only when a `.git` folder
        exists in the current directory
        """
        template = Config.render(config_file)
        template_env = dict(
            env=Config.env,
            git=Config.git_config(),
            git_branch=Config._git_branch(),
            git_commit=Config._git_commit())
        try:
            return yaml.load(template.render(**template_env))
        except jinja2.exceptions.UndefinedError as err:
            click.secho('[ERROR] {0} in {1}'.format(err.message, config_file), err=True, fg='red')
            exit(1)

    @staticmethod
    def render(config_file):
        path, filename = os.path.split(os.path.abspath(config_file))
        try:
            return jinja2.Environment(
                loader=jinja2.FileSystemLoader(path or './'),
                undefined=jinja2.StrictUndefined).get_template(filename)
        except jinja2.exceptions.TemplateNotFound:
            click.secho('[ERROR] No such file or directory: {0}'.format(config_file), err=True, fg='red')
            exit(1)
