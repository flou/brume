Brume: an AWS CloudFormation deployer
=====================================

.. image:: https://img.shields.io/travis/flou/brume.svg
    :target: https://travis-ci.org/flou/brume

.. image:: https://img.shields.io/pypi/v/brume.svg
    :target: https://pypi.python.org/pypi/brume

.. image:: https://img.shields.io/pypi/l/brume.svg
    :target: https://pypi.python.org/pypi/brume

.. image:: https://img.shields.io/pypi/wheel/brume.svg
    :target: https://pypi.python.org/pypi/brume

.. image:: https://img.shields.io/pypi/pyversions/brume.svg
    :target: https://pypi.python.org/pypi/brume

-------------------------------------

Installation
------------

brume is a Python package and it can be installed with Pip::

    $ pip install brume

Usage
-----

In order to use the commands, the current directory must contain a valid configuration file.

::

    Usage: brume [OPTIONS] COMMAND [ARGS]...

    Options:
      -v, --version          Show the version and exit.
      -h, --help             Show this message and exit.
      -c, --config FILENAME  Configuration file (defaults to brume.yml).

    Commands:
      check       Check CloudFormation templates.
      config      Print the current stack configuration.
      create      Create a new CloudFormation stack.
      delete      Delete the CloudFormation stack.
      deploy      Create or update a CloudFormation stack.
      outputs     Get the full list of outputs of a CloudFormation stack.
      parameters  Get the full list of parameters of a CloudFormation stack.
      status      Get the status of a CloudFormation stack.
      update      Update an existing CloudFormation stack.
      upload      Upload CloudFormation templates and assets to S3
      validate    Validate CloudFormation templates.

These commands always use the current AWS credentials and the stack name from the configuration file (via the ``--config`` option).


The ``brume.yml`` file
----------------------

The configuration file requires two configuration blocks ``stack`` and ``templates``.

Stack
~~~~~

::

    stack:
      stack_name: my-wordpress-website   # [REQUIRED] the name of the CloudFormation stack
      template_body: Main.cform          # local path to the main CloudFormation template
      template_url: https://my-bucket.s3.amazonaws.com/assets/cloudformation/Main.cform  # complete URL to the main CloudFormation template on S3

The template referenced in ``stack.template_body`` or ``stack.template_url`` is the entrypoint to your CloudFormation stack (the main or parent stack).

Templates
~~~~~~~~~

In case your stack is split between multiple templates, you need to upload the CloudFormation templates to S3 (e.g. using ``brume upload`` or the tool of your choice).

If you use ``brume upload``, you need to tell brume where the templates are and where to put them. This is done via the ``templates`` section.

::

    templates:
      s3_bucket: my-bucket            # [REQUIRED] name of the bucket in your account in which to store the templates
      s3_path: assets/cloudformation  # path of the S3 folder where the template are uploaded, defaults to `cloudformation`
      local_path: project/cfn         # local path where your CloudFormation templates are, defaults to `.`

Given the above configuration and if you have a ``Main.cform`` in ``project/cfn``, the template would be uploaded to ``https://my-bucket.s3.amazonaws.com/assets/cloudformation/Main.cform``.

Assets
~~~~~~

If 'assets' configuration is present you can send additionnal resources to
target s3 URI (like user data script, application config file, ...).

In your template, you can build assets url like this:

::

    def getAssetUri(asset, bucketName, stackName):
      return '/'.join(['s3://{}'.format(bucketName), stackName, 'assets', asset])



Minimal example
~~~~~~~~~~~~~~~

::

    region: eu-west-1

    stack:
      stack_name: my-wordpress-website
      template_body: Main.cform

    templates:
      s3_bucket: my-bucket

Complete example
~~~~~~~~~~~~~~~~

``brume.yml`` is in fact a Jinja2 template which means you can declare variables and reuse them in the template. You can also inject environment variables by calling ``{{ env('MY_VAR') }}``.

If the environment variable ``$MY_VAR`` does not exist, you can specify a fallback value by passing a second parameter ``{{ env('MY_VAR', 'FOO') }}``.

Also, if the current directory is a git repository (if it contains a ``.git/`` directory), ``brume`` exposes a ``dict`` named ``git``, that has the three following properties:

* ``git.commit_sha1`` : the SHA1 of the last commit
* ``git.branch_name`` : the name of the current branch (warning: if you are in detached mode, the branch name does not exist so it will be HEAD)
* ``git.commit_msg`` : the commit message of the last commit

It also exposes two previously available variables: ``git_commit`` and ``git_branch``

Their values are taken directly from the current repository.

::

    region: {{ env('AWS_REGION') }}

    {% set stack_name = '-'.join([env('PROJECT'), env('ENVIRONMENT'), env('CLASSIFIER')]) %}
    stack:
      stack_name: {{ stack_name }}

      template_body: Main.cform
      capabilities: [ CAPABILITY_IAM ]
      on_failure: DELETE

      parameters:
        Project: '{{ env('PROJECT') }}'
        Platform: '{{ env('PLATFORM') }}'
        Classifier: '{{ env('CLASSIFIER') }}'
        GitCommit: '{{ git_commit }}'
        GitBranch: '{{ git_branch }}'

      tags:
        Project: '{{ env('PROJECT') }}'
        Platform: '{{ env('PLATFORM') }}'
        Classifier: '{{ env('CLASSIFIER') }}'

    templates:
      s3_bucket: my_bucket
      s3_path: {{ stack_name }}
      local_path: cloudformation

    assets:
      s3_bucket: my_bucket
      s3_path: {{ stack_name }}/assets
      local_path: assets
