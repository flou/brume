import os # NOQA
from glob import glob
from brume.template import Template
from jinja2 import Template as Jinja


def gather_templates(dir='.'):
    return [Template(t) for t in glob('*.cform')]


def validate_templates(templates):
    for t in templates:
        t.validate()


def upload_templates(templates, bucket, path_prefix):
    validate_templates(templates)
    for t in templates:
        t.upload(bucket, path_prefix)


def env(key):
    return os.getenv(key, None)

template = Jinja(open('brume.yml', 'r').read())
print template.render(env=env)
