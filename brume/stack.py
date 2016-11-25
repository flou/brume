import time
import boto3
from color import Color
from colors import red
from botocore.exceptions import ClientError
from argparse import ArgumentParser

client = boto3.client('cloudformation')


class Stack():
    def __init__(self, stack_name):
        self.stack_name = stack_name
        self.url = None

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

    def create(self, stack_name):
        client.create_stack(
            StackName=stack_name,
        )

    def delete(self, stack_name):
        client.create_stack(
            StackName=stack_name,
        )

    def update(self, stack_name):
        pass

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


def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(
        description='Compile your configuration to CloudFormation templates.')
    parser.add_argument('-s', '--stack-name', required=True, help='The stack')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    Stack(args.stack_name).tail()
