Brume: an AWS CloudFormation deployer
=====================================

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

The current directory must contain a ``brume.yml`` configuration file.

Available commands
------------------

These commands always use the current AWS credentials and the stack name from the `brume.yml` file.

* ``config``: Print the current stack configuration based on the `brume.yml` file, with the variables interpolated.
* ``create``: Create the CloudFormation stack.
* ``delete``: Delete the CloudFormation stack.
* ``deploy``: Create or update the CloudFormation stack, if you only care about applying your changes and don't want to know if the stack already exists or not (can be useful for automated deployments)
* ``update``: Update the existing CloudFormation stack.
* ``upload``: Upload CloudFormation templates to S3.
* ``validate``: Validate the CloudFormation templates that reside in ``local_path`` (in the YAML configuration) or the current directory.
* ``outputs``: Get the full list of outputs
* ``parameters``: Get the full list of parameters

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

If 'assets' configuration is present you can send additionnal resource to target s3 URI (like user data script, application config file, ...).

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

Also, if the current directory is a git repository (if it contains a ``.git/`` directory), ``brume`` offers two pre-defined variables: ``git_commit`` and ``git_branch``.
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
