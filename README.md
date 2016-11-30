## Installation

brume is a Python package and it can be installed with Pip.

```sh
$ pip install brumecli
```

## Usage

The current directory must contain a `brume.yml` configuration file.

### Available commands

These commands always use the current AWS credentials and the stack name from the `brume.yml` file.

* `config`: Print the current stack confguration based on the `brume.yml` file.
* `create`: Create the CloudFormation stack.
* `delete`: Delete the CloudFormation stack.
* `deploy`: Create or update the CloudFormation stack, if you only care about applying your changes and don't want to know if the stack already exists or not (can be useful for automated deployments)
* `update`: Update the existing CloudFormation stack.
* `upload`: Upload CloudFormation templates to S3.
* `validate`: Validate the CloudFormation templates that reside in `local_path` (in the YAML configuration) or the current directory.

### Minimal example

```yaml
---
region: eu-west-1

stack:
  stack_name: Main
  template_body: Main.cform

templates:
  s3_bucket: my_bucket
```

### Complex example

`brume.yml` is in fact a Jinja2 template and can embed environment variable by calling `{{ env('MY_VAR') }}`.

Also, if the current directory is a git repository (if it contains a `.git/` directory), brume offers two pre-defined variables: `git_commit` and `git_branch`.
Their values are taken directly from the current repository.

```yaml
---
region: {{ env('AWS_REGION') }}

stack:
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
  s3_prefix: *stack_name
  local_path: cloudformation
```
