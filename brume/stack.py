import time
import os
import boto3
from color import Color
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
        self.parameters = make_parameters(conf.get('parameters', self.parameters))
        self.tags = make_tags(conf['tags'])
        self.on_failure = conf.get('on_failure', self.on_failure)

    def stack_exists(self):
        try:
            client.describe_stacks(StackName=self.stack_name)
        except ClientError as e:
            print(red('Stack [{}] does not exist'.format(self.stack_name)))
            raise e
            # return False
        else:
            return True

    def describe_resources():
        pass

    def create(self):
        print('Deploying stack {}'.format(self.stack_name))
        client.create_stack(
            StackName=self.stack_name,
            TemplateBody=open(self.template_body, 'r').read(),
            Parameters=self.parameters,
            Capabilities=self.capabilities,
            Tags=self.tags,
        )

    def update(self):
        print('Updating stack {}'.format(self.stack_name))
        client.update_stack(
            StackName=self.stack_name,
            TemplateBody=open(self.template_body, 'r').read(),
            Parameters=self.parameters,
            Capabilities=self.capabilities,
            Tags=self.tags,
        )

    def create_or_update(self):
        print('Applying stack {}'.format(self.stack_name))
        stack_configuration = dict(
            StackName=self.stack_name,
            TemplateBody=open(self.template_body, 'r').read(),
            Parameters=self.parameters,
            Capabilities=self.capabilities,
            Tags=self.tags)

        try:
            client.create_stack(stack_configuration)
        except ClientError:
            print('Stack {} already exists, updating it'.format(self.name))
            client.update_stack(stack_configuration)

    # def delete(self):
    #     print('Not implemented')
    #     pass

    def get_events(self):
        self.stack_exists()
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
        try:
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
                if self.stack_complete(e):
                    break
                time.sleep(sleep_time)
        except ClientError as e:
            # The stack does not exist
            pass

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
        print('{:23s} {:49s} {:30s} {:30s} {}'.format(
            e['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            Color.for_status(e['ResourceStatus']),
            e['LogicalResourceId'],
            e['ResourceType'],
            e.get('ResourceStatusReason', ''),
        ))
