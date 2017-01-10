import os
import yaml

from subprocess import check_output, CalledProcessError
from colors import red
from jinja2 import Template


class Config():

    @staticmethod
    def env(key):
        """Return the value of the `key` environment variable."""
        try:
            return os.environ[key]
        except KeyError:
            print(red('[ERROR] No environment variable with key {}'.format(key)))
            exit(1)

    @staticmethod
    def git_commit():
        """Return the SHA1 of the latest Git commit (HEAD)."""
        try:
            return check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
        except CalledProcessError:
            print(red('[ERROR] Current directory is not a Git repository'))
            exit(1)

    @staticmethod
    def git_branch():
        """Return the name of the current Git branch."""
        try:
            return check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
        except CalledProcessError:
            print(red('[ERROR] Current directory is not a Git repository'))
            exit(1)

    @staticmethod
    def load(config_file='brume.yml'):
        """
        Return the YAML configuration for a project based on the `config_file` template.

        By default, the template exposes the `env` function.
        The `git_branch` and `git_commit` values are exposed only when a `.git` folder
        exists in the current directory
        """
        template_functions = {}
        template_functions['env'] = Config.env

        if os.path.isdir('.git'):
            template_functions['git_commit'] = Config.git_commit()
            template_functions['git_branch'] = Config.git_branch()

        template = Template(open(config_file, 'r').read())
        return yaml.load(
            template.render(**template_functions)
        )
