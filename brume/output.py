"""
Output stack utility.

"""

import click
from botocore.exceptions import ClientError
from brume.boto_client import cfn_client


def _stack_walker(client, outputs, stack, collector):
    """
    :param client: cloudformation client
    :param outputs: current collected output
    :param stack: current stack name
    :param collector: function (outputs, description)
    :return: aggregated output
    Map collector function on stack and nested stack.
    """
    try:
        description = client.describe_stacks(StackName=stack)['Stacks'][0]
        collector(outputs, description)
        substacks = [s for s in client.describe_stack_resources(StackName=stack)[
            'StackResources'] if s['ResourceType'] == 'AWS::CloudFormation::Stack']
        for s in substacks:
            outputs[s['LogicalResourceId']] = {}
            _stack_walker(
                client, outputs[s['LogicalResourceId']], s['PhysicalResourceId'], collector)
        return outputs
    except ClientError as e:
        if 'does not exist' in e.message:
            click.secho('Stack [{}] does not exist'.format(
                stack), err=True, fg='red')
            exit(1)
        else:
            raise e


def _output_collector(outputs, description):
    """
    aggregate Outputs key/value from description
    """
    for o in description.get('Outputs', []):
        outputs[o['OutputKey']] = o['OutputValue']


def stack_outputs(region, stack_name):
    """Return specified stack outputs."""
    return _stack_walker(cfn_client(region=region), {}, stack_name, _output_collector)
