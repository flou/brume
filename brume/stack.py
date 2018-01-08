"""Stack."""

import time
from datetime import datetime, timedelta

import click
import crayons
import pytz
from botocore.exceptions import ClientError

from brume.boto_client import cfn_client
from brume.color import Color
from brume.config import Config
from brume.template import Template

TZ = pytz.timezone('UTC')


def _print_log_headers():
    click.echo('{:23s} {:36s} {:30s} {:30s} {}'.format(
        'Timestamp', 'Status', 'Resource', 'Type', 'Reason'
    ))


def _log_event(event):
    click.echo('{:23s} {:36s} {:30s} {:30s} {}'.format(
        event['Timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC'),
        Color.for_status(event['ResourceStatus']),
        event['LogicalResourceId'],
        event['ResourceType'],
        event.get('ResourceStatusReason', ''),
    ))


def _make_tags(tags_list):
    return [{'Key': k, 'Value': v} for k, v in tags_list.items()]


def _make_parameters(params_list):
    return [{'ParameterKey': k, 'ParameterValue': v} for k, v in params_list.items()]


def _outputs_for(stack):
    try:
        outputs = cfn_client().describe_stacks(StackName=stack)['Stacks'][0].get('Outputs', {})
        return {o['OutputKey']: o['OutputValue'] for o in outputs}
    except ClientError as e:
        if 'does not exist' in e.message:
            click.secho('Stack [{0}] does not exist'.format(stack), err=True, fg='red')
            exit(1)
        else:
            raise e


class Stack(object):
    """Represent a CloudFormation stack."""

    stack_name = None
    capabilities = []

    def __init__(self, conf):
        self.stack_name = conf['stack_name']
        self.template_body = conf['template_body']
        self.on_failure = conf.get('on_failure', 'ROLLBACK')
        self.capabilities = conf.get('capabilities', [])
        self.parameters = _make_parameters(conf.get('parameters', {}))
        self.tags = _make_tags(conf.get('tags', {}))
        self.main_template = Template(self.template_body, Config.config['templates'])

        # Check the events 10 seconds before if the stack update starts way too soon
        self.update_started_at = datetime.now(TZ) - timedelta(seconds=10)

    @property
    def configuration(self):
        stack_cfg = dict(
            StackName=self.stack_name,
            Parameters=self.parameters,
            Capabilities=self.capabilities,
            Tags=self.tags,
        )
        if self.main_template.template_is_too_large:
            stack_cfg['TemplateURL'] = self.main_template.public_url
        else:
            stack_cfg['TemplateBody'] = self.main_template.content
        return stack_cfg

    def get_stacks(self):
        """Return a list of stacks containing the current stack and its nested stack resources."""
        stacks = [self.stack_name]
        substacks = cfn_client().describe_stack_resources(StackName=self.stack_name)
        stacks.extend([
            s['PhysicalResourceId']
            for s in substacks['StackResources']
            if s['ResourceType'] == 'AWS::CloudFormation::Stack'
        ])
        return stacks

    def outputs(self):
        """
        Return a dict containing the outputs of the current stack and its nested stacks.
        """
        outputs = {self.stack_name: _outputs_for(self.stack_name)}
        stack_resources = cfn_client().describe_stack_resources(StackName=self.stack_name)
        outputs.update({
            res['LogicalResourceId']: _outputs_for(res['PhysicalResourceId'])
            for res in stack_resources['StackResources']
            if res['ResourceType'] == 'AWS::CloudFormation::Stack'
        })
        return outputs

    def params(self):
        """
        Return a dict containing the parameters of the current stack and its nested stacks.
        """
        try:
            return {
                stack: {
                    param['ParameterKey']: param['ParameterValue']
                    for param in cfn_client().describe_stacks(StackName=stack)['Stacks'][0].get('Parameters', [])
                } for stack in self.get_stacks()
            }
        except ClientError as e:
            if 'does not exist' in e.message:
                click.secho('Stack [{0}] does not exist'.format(self.stack_name), err=True, fg='red')
                exit(1)
            else:
                raise e

    @staticmethod
    def exists(stack_name):
        """
        Return `True` if a stack exists with the name `stack_name`, `False` otherwise.
        """
        try:
            cfn_client().describe_stacks(StackName=stack_name)
        except ClientError as e:
            if 'does not exist' in e.message:
                return False
        else:
            return True

    def create(self):
        """
        Create the stack in CloudFormation.
        """
        click.echo('Creating stack {0}...'.format(self.stack_name))
        try:
            cfn_client().create_stack(**self.configuration)
            time.sleep(5)
            self.tail()
        except ClientError as err:
            if 'AlreadyExistsException' in err.message:
                click.secho('Stack [{0}] already exists'.format(self.stack_name), err=True, fg='red')
                exit(1)
            else:
                click.secho(err.message, err=True, fg='red')

    def update(self):
        """
        Update the stack in CloudFormation if it exists.
        """
        click.echo('Updating stack {0}...'.format(self.stack_name))
        try:
            cfn_client().update_stack(**self.configuration)
            self.tail()
        except ClientError as err:
            if 'does not exist' in err.message:
                click.secho('Stack [{0}] does not exist'.format(self.stack_name), err=True, fg='red')
                exit(1)
            elif 'No updates are to be performed.' in err.message:
                click.echo(crayons.yellow('No updates are to be performed on stack [{}]'.format(
                    self.stack_name)), err=True)
                exit(1)
            else:
                click.secho(err.message, err=True, fg='red')

    def create_or_update(self):
        """
        Create or update the stack in CloudFormation if it already exists.
        """
        if Stack.exists(self.stack_name):
            self.update()
        else:
            self.create()

    def delete(self):
        """
        Delete the stack in CloudFormation.
        """
        click.echo('Deleting stack {0}...'.format(self.stack_name))
        if Stack.exists(self.stack_name):
            cfn_client().delete_stack(StackName=self.stack_name)
            try:
                self.tail(catch_error=True)
                click.echo(crayons.yellow('Stack [{0}] is deleted'.format(self.stack_name)))
            except ClientError as err:
                raise err
        else:
            click.secho('Stack [{0}] does not exist'.format(self.stack_name), err=True, fg='red')
            exit(1)

    def status(self):
        """
        Return the status of the stack in CloudFormation, based on the last stack event.
        """
        try:
            stacks = cfn_client().describe_stacks(StackName=self.stack_name)
            click.echo(Color.for_status(next(s['StackStatus'] for s in stacks['Stacks'])))
        except KeyError as err:
            click.secho(err, err=True, fg='red')
            exit(1)
        except ClientError as err:
            if 'does not exist' in err.message:
                click.secho('Stack [{}] does not exist'.format(self.stack_name), err=True, fg='red')
                exit(1)

    def get_events(self):
        """
        Fetch the stack events
        """
        events = cfn_client().describe_stack_events(StackName=self.stack_name)
        return reversed(events['StackEvents'])

    def tail(self, sleep_time=3, catch_error=False):
        """
        Tail the event log of the stack.
        """
        error = False
        seen = set()
        try:
            events = self.get_events()
            _print_log_headers()
            while True:
                for event in events:
                    if event['Timestamp'] < self.update_started_at:
                        seen.add(event['EventId'])
                    if event['EventId'] in seen:
                        continue
                    if 'FAILED' in event['ResourceStatus']:
                        error = True
                    _log_event(event)
                    seen.add(event['EventId'])
                if self.stack_complete(event):
                    if error:
                        exit(1)
                    break
                time.sleep(sleep_time)
                events = self.get_events()
        except ClientError as err:
            if 'does not exist' in err.message and catch_error:
                return False
            else:
                raise err

    def stack_complete(self, event):
        """
        Return True if the stack has reached a COMPLETE status.
        """
        return (
            event['LogicalResourceId'] == self.stack_name and
            event['ResourceStatus'].endswith('COMPLETE')
        )
