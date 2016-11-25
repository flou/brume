# from os import curdir
from subprocess import call
from glob import glob
# from brume.stack import Stack
from brume.template import Template


def gather_templates(dir='.'):
    return [Template(t) for t in glob('*.cform')]


def validate_templates(templates):
    for t in templates:
        t.validate()


def upload_templates(templates, bucket, path_prefix):
    validate_templates(templates)
    for t in templates:
        t.upload(bucket, path_prefix)


# bucket = 'iamflou'
# path_prefix = 'cloudformation'
# templates = gather_templates(curdir)
# validate_templates(templates)
# upload_templates(templates, bucket, path_prefix)
git_branch = call(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
print(git_branch)
