"""
cfn-check
"""
import os
import sys
import logging
import json
import click
import crayons

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CFN_REF = 'Ref'
CFN_GETATT = 'Fn::GetAtt'


class Stack(object):
    """docstring for Stack."""

    def __init__(self, name):
        self.name = name
        self.outputs = {}
        self.resources = {}
        self.template_url = ''

        # Parameters that are passed when declaring the stack as a resource
        # of the main stack
        self.input_parameters = {}

        # Parameters defined in the Parameters section of the template
        self.parameters = {}

    def find(self, key):
        """
        Return a list of resources and outputs that contain ``key``.
        """
        outputs_refs = list(Stack.find_nodes(self.outputs, key))
        resources_refs = list(Stack.find_nodes(self.resources, key))
        return resources_refs + outputs_refs

    def missing_refs(self):
        """
        Return a list of Ref statements that point to non-existing resources or
        parameters in the template.
        """
        return [ref for ref in self.find(CFN_REF) if not self.has_ref(ref)]

    def has_ref(self, ref):
        """
        Check that ``ref`` points to a resource that is actually declared in the
        template or in the parameters of the stack.
        """
        return ref in self.resources or ref in self.parameters

    def missing_getatt(self):
        """
        Return a list of GetAtt statements that point to non-existing resources
        or parameters in the template.
        """
        return [ref for ref in self.find(CFN_GETATT) if not self.has_getatt(ref)]

    def has_getatt(self, getatt):
        """
        Check that ``getatt`` points to a resource that is actually declared in
        the template or in the parameters of the stack.
        """
        return getatt[0] in self.resources or getatt[0] in self.parameters

    def missing_parameters(self):
        """
        Return a list of parameters that are expected in the substack with no
        default value but have no parameter in the main stack.
        """
        return [
            param_name
            for param_name, param in self.parameters.items()
            if param_name not in self.input_parameters and 'Default' not in param
        ]

    def extra_parameters(self):
        """
        Return a list of parameters that are passed from the main stack but are
        not expected in the substack definition.
        """
        return [
            param_name
            for param_name, _ in self.input_parameters.items()
            if param_name not in self.parameters
        ]

    def load_from_file(self, name=None):
        """
        Create a Stack from its template.
        """
        stack_name = name if name else self.name
        try:
            template = open(stack_name, 'r')
        except IOError as err:
            click.echo('Template for stack {0} not found'.format(stack_name), err=True)
            click.echo(err, err=True)
            sys.exit(1)
        template = json.load(template)
        self.outputs = template.get('Outputs', {})
        self.parameters = template.get('Parameters', {})
        self.resources = template.get('Resources', {})

    @staticmethod
    def new_substack(stack_name, resource):
        """
        Create a substack.
        """
        newstack = Stack(stack_name)
        newstack.input_parameters = resource['Properties'].get('Parameters', {})
        newstack.template_url = resource['Properties'].get('TemplateURL', {})
        return newstack

    @staticmethod
    def aws_pseudo_parameter(v):
        """
        Check that ``v`` is an AWS pseudo-parameter (like AWS::Region).
        """
        return isinstance(v, (str, unicode)) and v.startswith('AWS::')

    @staticmethod
    def find_nodes(node, key):
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            if Stack.aws_pseudo_parameter(v):
                continue
            if k == key:
                yield v
            elif isinstance(v, list):
                for n in v:
                    for id_val in Stack.find_nodes(n, key):
                        yield id_val
            elif isinstance(v, dict):
                for id_val in Stack.find_nodes(v, key):
                    yield id_val


def check_templates(template):
    """
    Checks:
    - that there are parameters sent from the main stack for every expected
      parameter in the substacks
    - that `Ref` and `GetAtt` point to existing resources or parameters in the
      template
    - that the outputs used as params in the main stack exist in the substacks
    """
    templates_path, filename = os.path.split(os.path.realpath(template))
    main_stack_name, filetype = os.path.splitext(filename)

    main_stack = Stack(main_stack_name)
    main_stack.load_from_file(os.path.join(templates_path, filename))

    stacks = {
        name: Stack.new_substack(name, resource)
        for name, resource in main_stack.resources.items()
        if resource['Type'] == 'AWS::CloudFormation::Stack'
    }
    stacks[main_stack_name] = main_stack

    error = 0
    for name, substack in stacks.items():
        substack_path = os.path.join(templates_path, name) + filetype
        LOGGER.debug('Loading Stack %s file %s', name, substack_path)
        substack.load_from_file(substack_path)

        if name != main_stack_name:
            # We don't validate Parameters on the Main stack
            for param in substack.missing_parameters():
                click.echo('Stack {0} should give substack {1} parameter: {2}'.format(
                    crayons.yellow(main_stack_name),
                    crayons.yellow(name),
                    crayons.red(param)
                ), err=True)
                error = 1
            for param in substack.extra_parameters():
                click.echo('Stack {0} is giving extra parameter {1} to substack: {2}'.format(
                    crayons.yellow(main_stack_name),
                    crayons.yellow(name),
                    crayons.red(param)
                ), err=True)
                error = 1

        for ref in substack.missing_refs():
            click.echo('Stack {0} has undefined {1} statement: {2}'.format(
                crayons.yellow(name), crayons.yellow('Ref'), crayons.red(ref)
            ), err=True)
            error = 1

        for getatt in substack.missing_getatt():
            click.echo('Stack {0} has undefined {1} statement: {2}'.format(
                crayons.yellow(name), crayons.yellow('GetAtt'), crayons.red(getatt)
            ), err=True)
            error = 1

    # Special case for the Main stack GetAtt
    for att in main_stack.find(CFN_GETATT):
        if att[1].startswith('Outputs.') and att[0] in stacks:
            stack = stacks[att[0]]
            output_name = att[1].replace('Outputs.', '')
            if output_name not in stacks[att[0]].outputs:
                click.echo('Stack {0} references undefined Output {1} from substack {2}'.format(
                    crayons.yellow(main_stack_name),
                    crayons.red(output_name),
                    crayons.yellow(stack.name)
                ), err=True)
                error = 1

    if not error:
        click.echo(crayons.green('Congratulations, your templates appear to be OK!\n'))
    else:
        sys.exit(error)
