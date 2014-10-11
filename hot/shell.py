""" hot is the command-line tool for testing Heat Templates """
import json
import os
import re
import signal
import string
import sys
import yaml

from argh import arg, alias, ArghParser
from heatclient.v1 import Client as heatClient
from time import sleep, time
from urlparse import urlparse

import hot.lint
import hot.tests
import hot.utils

from hot.utils.token import get_token
from hot.utils.catalog import get_service_endpoint


ENV_VARS = ['OS_PASSWORD', 'OS_USERNAME', 'OS_TENANT_ID', 'OS_AUTH_URL']

DOC_SECTIONS = ['parameters', 'outputs']


def verify_environment_vars(variables):
    for variable in variables:
        env_list = ', '.join([str(env) for env in ENV_VARS])
        if os.environ.get(variable):
            next
        elif variable == 'OS_PASSWORD':
            if not os.environ.get('OS_AUTH_TOKEN'):
                raise KeyError("Tool requires either OS_PASSWORD or OS_AUTH_TO"
                               "KEN to be set.")
        else:
            raise KeyError("%s not set. Tool requires the following enviro"
                           "nmental variables to be set %s" % (variable,
                                                               env_list))


@alias('docs')
@arg('--template', default='.catalog')
def do_create_docs(args):
    """Generate the basics for the README.md based on the information in a
    given template.
    """
    verified_template_directory = hot.utils.repo.check(args)
    template_attr = getattr(args, 'template')
    path_to_template = os.path.join(verified_template_directory, template_attr)
    try:
        raw_template = get_raw_yaml_file(args, file_path=path_to_template)
        validated_template = hot.utils.yaml.load(raw_template)
    except StandardError as exc:
        sys.exit(exc)
    # print validated_template['parameters']
    if 'description' in validated_template:
        print "Description\n===========\n\n%s\n" % \
              validated_template['description']
    if 'resources' in validated_template:
        resources = get_resource_types(validated_template['resources'])
        print "Requirements\n============\n* A Heat provider that supports th"\
              "e following:\n  * %s\n* An OpenStack username, password, and t"\
              "enant id.\n* [python-heatclient](https://github.com/openstack/"\
              "python-heatclient)\n`>= v0.2.8`:\n\n```bash\npip install pytho"\
              "n-heatclient\n```\n\nWe recommend installing the client within"\
              " a [Python virtual\nenvironment](http://www.virtualenv.org/)."\
              "\n" % '\n  * '.join(map(str, sorted(resources)))
    for section in DOC_SECTIONS:
        if section in validated_template:
            header = ""
            footer = ""
            if section is 'parameters':
                header = "Parameters\n==========\nParameters can be replaced "\
                         "with your own values when standing up a stack. Use"\
                         "\nthe `-P` flag to specify a custom parameter.\n"
            if section is 'outputs':
                header = "Outputs\n=======\nOnce a stack comes online, use `h"\
                         "eat output-list` to see all available outputs.\nUse"\
                         " `heat output-show <OUTPUT NAME>` to get the value "\
                         "of a specific output.\n"
                footer = "\nFor multi-line values, the response will come in "\
                         "an escaped form. To get rid of\nthe escapes, use `e"\
                         "cho -e '<STRING>' > file.txt`. For vim users, a sub"\
                         "stitution\ncan be done within a file using `%s/\\\\"\
                         "n/\\r/g`."
            convert_to_markdown(header, footer, validated_template[section])


def convert_to_markdown(header, footer, values):
    """Convert input to markdown format"""
    outputs = "%s" % header
    for value in values:
        key = value
        outputs = outputs + "\n* `%s`: " % key
        v = values[key]
        if 'description' in v:
            description = values[key]['description']
            outputs = outputs + "%s " % description
        if 'default' in v:
            default = values[key]['default']
            if isinstance(default, str) and len(default) == 0:
                default = "''"
            outputs = outputs + "(Default: %s)" % default
    outputs = outputs + "\n%s" % footer
    print outputs


def get_resource_types(resources):
    resources_list = set()
    for resource in resources:
        if 'type' in resources[resource]:
            resources_list.add(resources[resource]['type'])
    return resources_list


@alias('init')
@arg('project', help='name of the template project to begin')
@arg('-s', '--skeleton', default='https://github.com/brint/template-skeleton',
     help='git repo to clone when initializing this project')
@arg('-b', '--branch', help='optional: specify the branch to clone')
@arg('--no-git-init', default=False, help="Do not use 'git init' to initialize"
                                          " the project")
@arg('-v', '--verbose', default=False, help='show more verbose output while in'
                                            'itializing the project')
def do_template_init(args):
    """ Initialize a template project by cloning a skeleton repo.

    TODO: Implement verbose functionality
    """
    project = getattr(args, 'project')
    skeleton = getattr(args, 'skeleton')
    branch = getattr(args, 'branch')
    verbose = getattr(args, 'verbose')
    no_git = getattr(args, 'no_git_init')

    if hot.utils.string.valid_project_name(project):
        if branch:
            if hot.utils.repo.valid_branch_name(getattr(args, 'branch')):
                if no_git:
                    hot.utils.repo.clone_repo(skeleton, project, branch,
                                              'False')
                else:
                    hot.utils.repo.clone_repo(skeleton, project, branch)
            else:
                raise Exception("Invalid branch name: '%s'" %
                                getattr(args, 'branch'))
        else:
            if no_git:
                hot.utils.repo.clone_repo(skeleton, project, git_init=False)
            else:
                hot.utils.repo.clone_repo(skeleton, project)

    else:
        raise Exception("Invalid project name. Name must be a string <100 char"
                        "acters. Name provided: %s" % project)


@alias('lint')
@arg('--template', default='.catalog', help='Heat template to launch.')
@arg('--metadata', default='rackspace.yaml', help='Metadata file to audit')
def do_template_lint(args):
    """Check a template against a set of best practices"""
    verified_template_directory = hot.utils.repo.check(args)
    template = getattr(args, 'template')
    metadata = getattr(args, 'metadata')

    path_to_template = os.path.join(verified_template_directory, template)
    path_to_metadata = os.path.join(verified_template_directory, metadata)

    try:
        raw_template = get_raw_yaml_file(args, file_path=path_to_template)
        validated_template = hot.utils.yaml.load(raw_template)
        raw_metadata = get_raw_yaml_file(args, file_path=path_to_metadata)
        validated_metadata = hot.utils.yaml.load(raw_metadata)

    except StandardError as exc:
        sys.exit(exc)

    for rule_object_name in hot.lint.RULES:
        rule = getattr(hot.lint, rule_object_name)(validated_template,
                                                   validated_metadata)
        rule.check()


@alias('test')
@arg('--template', default='.catalog', help='Heat template to launch.')
@arg('--tests-file', default='tests.yaml', help='Test file to use.')
@arg('-k', '--keep-failed', default=False, help='Do not delete a failed test '
                                                'deployment.')
@arg('-s', '--sleep', default=15, type=int, help='Frequency for checking test '
                                                 'stack status.')
@arg('--test-cases', nargs='+', type=str, help='Space delimited list of '
                                               'tests to run. If none are '
                                               'specified, all will be run.')
def do_template_test(args):
    """ Test a template by going through the test scenarios in 'tests.yaml' or
    the tests file specified by the user
    """
    verified_template_directory = hot.utils.repo.check(args)
    template_attr = getattr(args, 'template')
    tests_attr = getattr(args, 'tests_file')
    test_cases = getattr(args, 'test_cases')
    sleeper = getattr(args, 'sleep')
    path_to_template = os.path.join(verified_template_directory, template_attr)
    path_to_tests = os.path.join(verified_template_directory, tests_attr)
    try:
        verify_environment_vars(ENV_VARS)
        raw_template = get_raw_yaml_file(args, file_path=path_to_template)
        validated_template = hot.utils.yaml.load(raw_template)
        raw_tests = get_raw_yaml_file(args, file_path=path_to_tests)
        validated_tests = hot.utils.yaml.load(raw_tests)
        tests = validated_tests['test-cases']
    except StandardError as exc:
        sys.exit(exc)

    auth_token = os.environ.get('OS_AUTH_TOKEN')
    if not auth_token:
        os_password = os.environ['OS_PASSWORD']
        auth_token = get_token(os.environ['OS_AUTH_URL'],
                               os.environ['OS_USERNAME'],
                               password=os_password)

    heat_region = os.environ.get('OS_REGION_NAME')
    heat_url = os.environ.get('HEAT_URL')
    if not heat_url:
        heat_url = get_service_endpoint(heat_region,
                                        'cloudOrchestration',
                                        os.environ['OS_AUTH_URL'],
                                        os.environ['OS_USERNAME'],
                                        password=os_password)
        if not heat_url:
            raise Exception("No heat endpoint found "
                            "for region {}".format(heat_region))

    hc = heatClient(endpoint=heat_url, token=auth_token)

    if test_cases:
        user_tests = []
        for case in test_cases:
            for test in tests:
                if test['name'] == case:
                    user_tests.append(test)
        if not user_tests or len(user_tests) < len(test_cases):
            user_defined_tests = ', '.join([str(t) for t in test_cases])
            sys.exit("Error: One or more of the following test cases not "
                     "found: %s" % user_defined_tests)
        tests = user_tests
    for test in tests:
        stack = launch_test_deployment(hc, validated_template, test,
                                       args.keep_failed, sleeper)
        if 'resource_tests' in test:
            try:
                run_resource_tests(hc, stack['stack']['id'],
                                   test)
                print "  Test Passed!"
            except:
                exctype, value = sys.exc_info()[:2]
                delete_test_deployment(hc, stack, args.keep_failed)
                sys.exit("Test Failed! %s: %s" %
                         (exctype, value))
        delete_test_deployment(hc, stack)


def run_resource_tests(hc, stack_id, resource_tests):
    stack_info = hc.stacks.get(stack_id)
    outputs = stack_info.to_dict().get('outputs', [])
    # Sub out {get_output: value} lines
    resource_tests = update_dict(resource_tests['resource_tests'], outputs)

    # For debugging purposes
    # print resource_tests

    if 'ssh_key_file' in resource_tests:
        ssh_key_file = resource_tests['ssh_key_file']
    else:
        ssh_key_file = 'tmp/private_key'

    # If the file path specified does not exist, create it.
    if not os.path.exists(os.path.dirname(ssh_key_file)):
        os.makedirs(os.path.dirname(ssh_key_file))

    if 'ssh_private_key' in resource_tests:
        with os.fdopen(os.open(ssh_key_file, os.O_WRONLY | os.O_CREAT, 0600),
                       'w') as handle:
            handle.write(resource_tests['ssh_private_key'])

    for test in resource_tests['tests']:
        test_name = test.keys()[0]
        # print test[test_name]
        if "fabric" in test[test_name]:
            hot.tests.fab.run_fabric_tasks(test_name, test[test_name])
        elif "script" in test[test_name]:
            hot.tests.script.run_script(test_name, test[test_name])
        else:
            print "  No tests defined."
    if 'ssh_private_key' in resource_tests:
        hot.utils.files.delete_file(ssh_key_file)


def update_dict(items, outputs):
    """Update dict based on user input.  This will take anything things like
       { get_output: server_ip } and replace it with the value of the given
       output.
    """
    try:
        for k, v in items.items():
            if isinstance(v, dict):
                items[k] = update_dict(v, outputs)
            elif isinstance(v, list):
                new_list = []
                for e in v:
                    new_list.append(update_dict(e, outputs))
                items[k] = new_list
            elif isinstance(v, int):
                items[k] = v
            elif k == 'get_output':
                return get_output(v, outputs)
            else:
                items[k] = v
    except:
        pass
    return items


def convert_to_array(value):
    """Converts string to array, if `value` is an array, returns `value`"""
    if isinstance(value, list):
        return value
    elif isinstance(value, basestring):
        return [value]


def get_output(key, outputs):
    for output in outputs:
        if output['output_key'] == key:
            return output['output_value']


def delete_test_deployment(hc, stack, keep_deployment=False):
    if keep_deployment:
        print "  Keeping %s up." % stack['stack']['id']
    else:
        print "  Deleting %s" % stack['stack']['id']
        hc.stacks.delete(stack['stack']['id'])


def launch_test_deployment(hc, template, test, keep_failed, sleeper):
    pattern = re.compile('[\W]')
    stack_name = pattern.sub('_', "%s-%s" % (test['name'], time()))
    data = {"stack_name": stack_name, "template": yaml.safe_dump(template)}

    timeout = get_create_value(test, 'timeout')
    parameters = get_create_value(test, 'parameters')
    retries = get_create_value(test, 'retries')  # TODO: Implement retries

    if timeout:
        timeout_value = timeout * 60
        signal.signal(signal.SIGALRM, hot.utils.timeout.handler)
        signal.alarm(timeout_value)
    if parameters:
        data.update({"parameters": parameters})

    print "Launching: %s" % stack_name
    stack = hc.stacks.create(**data)

    if timeout_value:
        print "  Timeout set to %s seconds." % timeout_value

    try:
        monitor_stack(hc, stack['stack']['id'], sleeper)
        if timeout_value:
            signal.alarm(0)
    except Exception:
        delete_test_deployment(hc, stack, keep_failed)
        sys.exit("Stack failed to deploy")
    return stack


def get_create_value(test, key):
    if key in test['create']:
        return test['create'][key]
    return None


def monitor_stack(hc, stack_id, sleeper=15):
    incomplete = True
    while incomplete:
        print "  Stack %s in progress, checking in %s seconds.." % (stack_id,
                                                                    sleeper)
        sleep(sleeper)
        status = hc.stacks.get(stack_id)
        if status.stack_status == u'CREATE_COMPLETE':
            incomplete = False
            print "  Stack %s built successfully!" % stack_id
        elif status.stack_status == u'CREATE_FAILED':
            stack_status = status.stack_status_reason
            print "  Stack %s build failed! Reason:\n  %s" % (stack_id,
                                                              stack_status)
            raise Exception("Stack build %s failed" % stack_id)


def get_raw_yaml_file(args, file_path=None):
    """

    Reads the contents of any YAML file in the repository as a string

    :param args: the hot call argument
    :param file_path: the file name with optional additional path
        (subdirectory) or as a URL
    :returns: the string contents of the file

    """
    # file can be a URL or a local file
    file_contents = None
    parsed_file_url = urlparse(file_path)
    if parsed_file_url.scheme == '':
        # Local file
        try:
            _file = open(os.path.expanduser(file_path))
            file_contents = _file.read()
            _file.close()
        except IOError as ioerror:
            raise IOError('Error reading %s. [%s]' % (file_path, ioerror))
    else:
        raise Exception('URL scheme %s is not supported.' %
                        parsed_file_url.scheme)

    return file_contents


def main():
    """Shell entry point for execution"""
    try:
        argparser = ArghParser()
        argparser.add_commands([
            do_template_test,
            do_create_docs,
            do_template_init,
            do_template_lint,
        ])

        argparser.dispatch()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
