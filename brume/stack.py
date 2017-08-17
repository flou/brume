"""
Stack.
"""

import time
from datetime import datetime, timedelta
import boto3
import click
import pytz
from brume.color import Color
import crayons

from botocore.exceptions import ClientError

client = boto3.client('cloudformation')
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


def _make_parameters(tags_list):
    return [{'ParameterKey': k, 'ParameterValue': v} for k, v in tags_list.items()]


def _outputs_for(outputs, stack):
    try:
        s_outputs = client.describe_stacks(StackName=stack)['Stacks'][0].get('Outputs', [])
        for o in s_outputs:
            outputs[o['OutputKey']] = o['OutputValue']
        return outputs
    except ClientError as e:
        if 'does not exist' in e.message:
            click.secho('Stack [{}] does not exist'.format(stack), err=True, fg='red')
            exit(1)
        else:
            raise e


class Stack(object):
    """
    Represent a CloudFormation stack.
    """

    stack_name = None
    capabilities = []

    def __init__(self, conf):
        self.stack_name = conf['stack_name']
        self.template_body = conf['template_body']
        self.parameters = _make_parameters(conf.get('parameters', {}))
        self.on_failure = conf.get('on_failure', 'ROLLBACK')

        # Check the events 2 minutes before if the stack update starts way too soon
        self.update_started_at = datetime.now(TZ) - timedelta(seconds=30)

        self.stack_configuration = dict(
            StackName=self.stack_name,
            TemplateBody=open(self.template_body, 'r').read(),
            Parameters=self.parameters,
            Capabilities=conf.get('capabilities', []),
            Tags=_make_tags(conf.get('tags', {})))

    def get_stacks(self):
        """
        Return a list of stacks containing the current stack and its nested stack resources.
        """
        stacks = [self.stack_name]
        substacks = client.describe_stack_resources(StackName=self.stack_name)['StackResources']
        stacks.extend([s['PhysicalResourceId'] for s in substacks])
        return stacks

    def outputs(self):
        """
        Return a dict containing the outputs of the current stack and its nested stacks.
        """
        outputs = {}
        _outputs_for(outputs, self.stack_name)
        substacks = client.describe_stack_resources(StackName=self.stack_name)['StackResources']
        for s in substacks:
            outputs[s['LogicalResourceId']] = {}
            _outputs_for(outputs[s['LogicalResourceId']], s['PhysicalResourceId'])
        return outputs

    def params(self):
        """
        Return a dict containing the parameters of the current stack and its nested stacks.
        """
        parameters = {}
        try:
            for stack in self.get_stacks():
                parameters[stack] = {}
                s_params = client.describe_stacks(StackName=stack)['Stacks'][0].get('Parameters', [])
                for o in s_params:
                    parameters[stack][o['ParameterKey']] = o['ParameterValue']
            return parameters
        except ClientError as e:
            if 'does not exist' in e.message:
                click.secho('Stack [{}] does not exist'.format(self.stack_name), err=True, fg='red')
                exit(1)
            else:
                raise e

    @staticmethod
    def exists(stack_name):
        """
        Return `True` if a stack exists with the name `stack_name`, `False` otherwise.
        """
        try:
            client.describe_stacks(StackName=stack_name)
        except ClientError as e:
            if 'does not exist' in e.message:
                return False
        else:
            return True

    def create(self):
        """
        Create the stack in CloudFormation.
        """
        click.echo('Creating stack {}...'.format(self.stack_name))
        try:
            client.create_stack(**self.stack_configuration)
            time.sleep(5)
            self.tail()
        except ClientError as err:
            if 'AlreadyExistsException' in err.message:
                click.secho('Stack [{}] already exists'.format(self.stack_name), err=True, fg='red')
                exit(1)
            else:
                click.secho(err.message, err=True, fg='red')

    def update(self):
        """
        Update the stack in CloudFormation if it exists.
        """
        click.echo('Updating stack {}...'.format(self.stack_name))
        try:
            client.update_stack(**self.stack_configuration)
            self.tail()
        except ClientError as err:
            if 'does not exist' in err.message:
                click.secho('Stack [{}] does not exist'.format(self.stack_name), err=True, fg='red')
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
            client.delete_stack(StackName=self.stack_name)
            try:
                self.tail(catch_error=True)
                click.echo(crayons.yellow('Stack [{0}] is deleted'.format(self.stack_name)))
            except ClientError as err:
                raise err
        else:
            click.secho('Stack [{}] does not exist'.format(self.stack_name), err=True, fg='red')
            exit(1)

    def status(self):
        """
        Return the status of the stack in CloudFormation, based on the last stack event.
        """
        try:
            stacks = client.describe_stacks(StackName=self.stack_name)
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
        events = client.describe_stack_events(StackName=self.stack_name)
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
