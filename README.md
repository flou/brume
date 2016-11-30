## Installation

brume is a Python package and it can be installed with Pip.

```sh
$ pip install brumecli
```

## Usage

The current directory must contain a `brume.yml` configuration file.

### Available commands

These commands always use the current AWS credentials and the stack name from the `brume.yml` file.

* `config`: Print the current stack configuration based on the `brume.yml` file, with the variables interpolated.
* `create`: Create the CloudFormation stack.
* `delete`: Delete the CloudFormation stack.
* `deploy`: Create or update the CloudFormation stack, if you only care about applying your changes and don't want to know if the stack already exists or not (can be useful for automated deployments)
* `update`: Update the existing CloudFormation stack.
* `upload`: Upload CloudFormation templates to S3.
* `validate`: Validate the CloudFormation templates that reside in `local_path` (in the YAML configuration) or the current directory.

## The `brume.yml` file

The configuration file requires two configuration blocks `stack` and `templates`.

### Stack

```yaml
stack:
  stack_name: my-wordpress-website                             # the name of the CloudFormation stack
  template_body: Main.cform                                    # local path to the main CloudFormation template
  template_url: https://my-bucket.s3.amazonaws.com/Main.cform  # complete URL to the main CloudFormation template on S3
```

The template referenced in `stack.template_body` or `stack.template_url` is the entrypoint to your CloudFormation stack (the main or parent stack).

### Templates

In case your stack is split between multiple templates, you need to upload the CloudFormation templates to S3 (e.g. using `brume upload` or the tool of your choice).

If you use `brume upload`, you need to tell brume where the templates are and where to put them. This is done via the `templates` section.

```yaml
templates:
  s3_bucket: my-bucket                # name of the bucket in your account in which to store the templates
  s3_prefix: assets/cloudformation    # the prefix that will be the path of every template on S3
  local_path: project/cloudformation  # local path where your CloudFormation templates are
```

Given the above configuration and if you have a `Main.cform` in the `project/cloudformation`, the template would be uploaded to `https://my-bucket.s3.amazonaws.com/assets/cloudformation/Main.cform`.

### Minimal example

```yaml
---
region: eu-west-1

stack:
  stack_name: my-wordpress-website
  template_body: Main.cform

templates:
  s3_bucket: my-bucket
```

### Complete example

`brume.yml` is in fact a Jinja2 template and can embed environment variable by calling `{{ env('MY_VAR') }}`.

Also, if the current directory is a git repository (if it contains a `.git/` directory), brume offers two pre-defined variables: `git_commit` and `git_branch`.
Their values are taken directly from the current repository.

```yaml
---
region: {{ env('AWS_REGION') }}

stack:
  # Since this is YAML we can define and anchor using the
  # &anchor notation and reuse this later in the template
  stack_name: &stack_name
    {{ '-'.join([env('PROJECT'), env('PLATFORM'), env('CLASSIFIER')]) }}

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
  s3_prefix: *stack_name     # This is a reference to &stack_name
  local_path: cloudformation
```
