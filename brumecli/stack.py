import time
import os
import boto3
from colors import red
from botocore.exceptions import ClientError

client = boto3.client('cloudformation')


def env(key):
    return os.getenv(key, None)


def make_tags(tags_list):
    return [{"Key": k, "Value": v} for k, v in tags_list.items()]


def make_parameters(tags_list):
    return [{"ParameterKey": k, "ParameterValue": v} for k, v in tags_list.items()]


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

        self.stack_configuration = dict(
            StackName=self.stack_name,
            TemplateBody=open(self.template_body, 'r').read(),
            Parameters=self.parameters,
            Capabilities=self.capabilities,
            Tags=self.tags)

    @staticmethod
    def exists(stack_name):
        try:
            client.describe_stacks(StackName=stack_name)
        except ClientError as e:
            # print(e)
            if 'AlreadyExistsException' in e.message:
                print(red('Stack [{}] does not exist'.format(stack_name)))
                exit(1)
            # return False
        else:
            return True

    def create(self):
        print('Deploying stack {}'.format(self.stack_name))
        try:
            client.create_stack(**self.stack_configuration)
            self.tail()
        except ClientError as e:
            if 'AlreadyExistsException' in e.message:
                print(red('Stack [{}] does not exist'.format(self.stack_name)))
                exit(1)

    def update(self):
        print('Updating stack {}'.format(self.stack_name))
        try:
            client.update_stack(**self.stack_configuration)
            self.tail()
        except ClientError as e:
            if 'does not exist' in e.message:
                print(red('Stack [{}] does not exist'.format(self.stack_name)))
                exit(1)
            if 'No updates are to be performed.' in e.message:
                print(red('No updates are to be performed on stack [{}]'.format(self.stack_name)))
                exit(1)

    def create_or_update(self):
        print('Applying stack {}'.format(self.stack_name))
        try:
            client.create_stack(**self.stack_configuration)
            self.tail()
        except ClientError as e:
            if 'does not exist' in e.message:
                print(red('Stack [{}] does not exist'.format(self.stack_name)))
                exit(1)
            if 'No updates are to be performed.' in e.message:
                print(red('No updates are to be performed on stack [{}]'.format(self.stack_name)))
                exit(1)
            print(e.message)
            print('Stack {} already exists'.format(self.stack_name))
            self.update()

    def delete(self):
        print('Deleting stack {}'.format(self.stack_name))
        try:
            client.delete_stack(StackName=self.stack_name)
            self.tail()
        except ClientError:
            # if 'does not exist' in e.message:
            exit(1)

    def get_events(self):
        Stack.exists(self.stack_name)
        event_list = []
        params = dict(StackName=self.stack_name)
        while True:
            events = client.describe_stack_events(**params)
            event_list.append(events)
            if 'NextToken' not in events:
                break
            params.NextToken = events.NextToken
            time.sleep(1)
        return reversed(event_list[0]['StackEvents'])

    def tail(self, sleep_time=5):
        print('Polling for events...')
        error = False
        seen = set()
        initial_events = self.get_events()
        self.print_log_headers()
        for e in initial_events:
            self._log_event(e)
            seen.add(e['EventId'])

        while True:
            events = self.get_events()
            for e in events:
                if e['EventId'] not in seen:
                    self._log_event(e)
                    seen.add(e['EventId'])
                    if 'FAILED' in e['ResourceStatus']:
                        error = True
            if self.stack_complete(e):
                if error:
                    exit(1)
                break
            time.sleep(sleep_time)

    def stack_complete(self, e):
        if e['LogicalResourceId'] == self.stack_name and e['ResourceStatus'].endswith('COMPLETE'):
            return True
        else:
            return False

    def print_log_headers(self):
        print('{:23s} {:36s} {:30s} {:30s} {}'.format(
            'Timestamp', 'Status', 'Resource', 'Type', 'Reason'
        ))

    def _log_event(self, e):
        print('{:23s} {:36s} {:30s} {:30s} {}'.format(
            e['Timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC'),
            e['ResourceStatus'],
            e['LogicalResourceId'],
            e['ResourceType'],
            e.get('ResourceStatusReason', ''),
        ))
