import time
import os
from datetime import datetime, timedelta
import boto3
import click
import pytz
from brume.color import Color

from botocore.exceptions import ClientError

client = boto3.client('cloudformation')
TZ = pytz.timezone('UTC')


def env(key):
    return os.getenv(key, None)


def make_tags(tags_list):
    return [{"Key": k, "Value": v} for k, v in tags_list.items()]


def make_parameters(tags_list):
    return [{"ParameterKey": k, "ParameterValue": v} for k, v in tags_list.items()]


def outputs_for(outputs, stack):
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


class Stack():
    stack_name = None
    parameters = {}
    capabilities = []
    tags = {}
    on_failure = 'ROLLBACK'

    def __init__(self, conf):
        self.stack_name = conf['stack_name']
        self.template_body = conf['template_body']
        self.capabilities = conf.get('capabilities', self.capabilities)
        self.parameters = make_parameters(conf.get('parameters', self.parameters))
        self.tags = make_tags(conf['tags'])
        self.on_failure = conf.get('on_failure', self.on_failure)

        # Check the events 2 minutes before if the stack update starts way too soon
        self.update_started_at = datetime.now(TZ) - timedelta(minutes=2)

        self.stack_configuration = dict(
            StackName=self.stack_name,
            TemplateBody=open(self.template_body, 'r').read(),
            Parameters=self.parameters,
            Capabilities=self.capabilities,
            Tags=self.tags)

    def get_stacks(self):
        stacks = [self.stack_name]
        substacks = client.describe_stack_resources(StackName=self.stack_name)['StackResources']
        stacks.extend([s['PhysicalResourceId'] for s in substacks])
        return stacks

    def outputs(self):
        outputs = {}
        outputs_for(outputs, self.stack_name)
        substacks = client.describe_stack_resources(StackName=self.stack_name)['StackResources']
        for s in substacks:
            outputs[s['LogicalResourceId']] = {}
            outputs_for(outputs[s['LogicalResourceId']], s['PhysicalResourceId'])
        return outputs

    def params(self):
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
        try:
            client.describe_stacks(StackName=stack_name)
        except ClientError as e:
            if 'AlreadyExistsException' in e.message:
                click.secho('Stack [{}] does not exist'.format(stack_name), err=True, fg='red')
                exit(1)
        else:
            return True

    def create(self):
        click.echo('Creating stack {}'.format(self.stack_name))
        try:
            client.create_stack(**self.stack_configuration)
            self.tail()
        except ClientError as e:
            if 'AlreadyExistsException' in e.message:
                click.secho('Stack [{}] already exists'.format(self.stack_name), err=True, fg='red')
                exit(1)

    def update(self):
        click.echo('Updating stack {}'.format(self.stack_name))
        try:
            client.update_stack(**self.stack_configuration)
            self.tail()
        except ClientError as e:
            if 'does not exist' in e.message:
                click.secho('Stack [{}] does not exist'.format(self.stack_name), err=True, fg='red')
                exit(1)
            if 'No updates are to be performed.' in e.message:
                click.secho('No updates are to be performed on stack [{}]'.format(self.stack_name), err=True, fg='red')
                exit(1)

    def create_or_update(self):
        click.echo('Deploying stack {}'.format(self.stack_name))
        try:
            client.create_stack(**self.stack_configuration)
            self.tail()
        except ClientError as e:
            if 'does not exist' in e.message:
                click.secho('Stack [{}] does not exist'.format(self.stack_name), err=True, fg='red')
                exit(1)
            if 'No updates are to be performed.' in e.message:
                click.secho('No updates are to be performed on stack [{}]'.format(self.stack_name), err=True, fg='red')
                exit(1)
            click.secho(e.message, err=True, fg='red')
            click.secho('Stack {} already exists'.format(self.stack_name), err=True, fg='red')
            self.update()

    def delete(self):
        click.echo('Deleting stack {}'.format(self.stack_name))
        try:
            client.delete_stack(StackName=self.stack_name)
            self.tail()
        except ClientError:
            # if 'does not exist' in e.message:
            exit(1)

    def status(self):
        try:
            stacks = client.describe_stacks(StackName=self.stack_name)
            click.echo(Color.for_status(next(s['StackStatus'] for s in stacks['Stacks'])))
        except KeyError as e:
            click.secho(e, err=True, fg='red')
            exit(1)
        except ClientError as e:
            if 'does not exist' in e.message:
                click.secho('Stack [{}] does not exist'.format(self.stack_name), err=True, fg='red')
                exit(1)

    def get_events(self):
        events = client.describe_stack_events(StackName=self.stack_name)
        return reversed(events['StackEvents'])

    def tail(self, sleep_time=3):
        error = False
        seen = set()
        click.echo('Polling for events...')
        self.print_log_headers()
        events = self.get_events()
        while True:
            for e in events:
                if e['Timestamp'] < self.update_started_at:
                    seen.add(e['EventId'])
                if e['EventId'] in seen:
                    continue
                if 'FAILED' in e['ResourceStatus']:
                    error = True
                self._log_event(e)
                seen.add(e['EventId'])
            if self.stack_complete(e):
                if error:
                    exit(1)
                break
            time.sleep(sleep_time)
            events = self.get_events()

    def stack_complete(self, e):
        if e['LogicalResourceId'] == self.stack_name and e['ResourceStatus'].endswith('COMPLETE'):
            return True
        else:
            return False

    def print_log_headers(self):
        click.echo('{:23s} {:36s} {:30s} {:30s} {}'.format(
            'Timestamp', 'Status', 'Resource', 'Type', 'Reason'
        ))

    def _log_event(self, e):
        click.echo('{:23s} {:36s} {:30s} {:30s} {}'.format(
            e['Timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC'),
            Color.for_status(e['ResourceStatus']),
            e['LogicalResourceId'],
            e['ResourceType'],
            e.get('ResourceStatusReason', ''),
        ))
